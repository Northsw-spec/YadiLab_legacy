"""Direct HTTP and real Chromium acceptance for automatic post-import ELK."""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from ods_fixture import make_ods
from xlsx_fixture import make_workbook
from test_csv_import import DEV, PORTS, LINKS, ZONES
from spreadsheet_v13_fixture import TABLES_13
from network_core.spreadsheet_templates import _xlsx as template_xlsx
from browser_elk_layout import paths_match_visible_ports


def no_coordinates(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    result = io.StringIO()
    writer = csv.DictWriter(result, fieldnames=('zoneId', 'kind', 'label', 'id'),
                            lineterminator='\n')
    writer.writeheader()
    writer.writerows({key: row[key] for key in writer.fieldnames} for row in rows)
    return result.getvalue()


def network(project):
    copy = json.loads(json.dumps(project))
    for node in copy['nodes']:
        del node['x'], node['y']
    return copy


def accept(dialog):
    if dialog.type == 'prompt':
        dialog.accept('Automatic layout')
    else:
        dialog.accept()


def wait_layout(page):
    page.wait_for_function("""() => document.querySelector('#layout-status').textContent
      .startsWith('Automatisk ELK-layout klar.') || document.querySelector('#layout-status').textContent
      .startsWith('Automatisk ELK-layout misslyckades:')""", timeout=30000)
    assert page.locator('#layout-status').inner_text().startswith(
        'Automatisk ELK-layout klar.'), page.locator('#layout-status').inner_text()
    assert page.locator('#layout-apply').is_disabled()


def run():
    with tempfile.TemporaryDirectory() as directory:
        store = ProjectStore(Path(directory))
        server = LabHTTPServer(('127.0.0.1', 0), store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                executable = shutil.which('chromium') or shutil.which('chromium-browser')
                browser = playwright.chromium.launch(headless=True, executable_path=executable,
                                                     args=['--no-sandbox'] if executable else [])
                page = browser.new_page(viewport={'width': 1440, 'height': 900})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('dialog', accept)
                page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
                page.locator('#count-nodes').wait_for(state='attached')
                page.evaluate("""() => document.querySelectorAll('[data-dropdown-card]')
                  .forEach(card => card.open = true)""")
                legacy = {'Devices': no_coordinates(DEV), 'Interfaces': PORTS,
                          'Links': LINKS, 'Zones': ZONES}
                rich = dict(TABLES_13, Devices=no_coordinates(TABLES_13['Devices']))
                documents = (
                    ('csv', legacy, 'pc-a'),
                    ('xlsx', make_workbook(rich, shared_strings=True), 'ha'),
                    ('ods', make_ods(rich, trailing=True), 'ha'),
                    ('xlsx', template_xlsx(), 'demo-client'),
                )
                for extension, payload, node_id in documents:
                    saved_name = 'auto-'+extension+('-template' if node_id == 'demo-client' else '')
                    files_before = sorted(Path(directory).glob('*.yadilab'))
                    if extension == 'csv':
                        files = [{'name': name+'.csv', 'mimeType': 'text/csv',
                                  'buffer': data.encode()} for name, data in payload.items()]
                    else:
                        files = {'name': 'network.'+extension, 'mimeType':
                                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                 if extension == 'xlsx' else
                                 'application/vnd.oasis.opendocument.spreadsheet', 'buffer': payload}
                    with page.expect_response('**/api/import/'+extension) as imported:
                        page.locator('#import-file').set_input_files(files)
                    assert imported.value.status == 200
                    incoming = imported.value.json()['project']
                    wait_layout(page)
                    assert page.locator('[data-node-id="'+node_id+'"]').count() == 1
                    assert sorted(Path(directory).glob('*.yadilab')) == files_before, 'import autosaved a file'
                    page.locator('#project-filename').fill(saved_name)
                    page.locator('#project-filename').dispatch_event('change')
                    with page.expect_response('**/api/save') as saved:
                        page.locator('#save-project').click()
                    assert saved.value.status == 200
                    actual = store.read(saved_name)['project']
                    assert network(actual) == network(incoming)
                    assert paths_match_visible_ports(page, actual)['endpointCount'] == 2 * len(actual['links'])
                    page.locator('#new-project').click()
                    page.locator('#saved-projects').select_option(saved_name)
                    page.locator('#open-project').click()
                    expect(page.locator('[data-node-id="'+node_id+'"]')).to_have_count(1)
                    assert page.locator('#layout-controls').is_hidden(), 'Open started ELK'
                    page.locator('#new-project').click()

                # A rejected strict document must not start ELK or replace the workspace.
                bad = dict(legacy, Devices='id,label,kind,x,zoneId\npc-a,Client,host,1,\n')
                with page.expect_response('**/api/import/csv') as rejected:
                    page.locator('#import-file').set_input_files([
                        {'name': name+'.csv', 'mimeType': 'text/csv', 'buffer': data.encode()}
                        for name, data in bad.items()])
                assert rejected.value.status == 422
                assert page.locator('#count-nodes').inner_text() == '0'
                assert page.locator('#layout-controls').is_hidden()

                # Flexible import: explicit mapping and approval start the same Worker.
                page.locator('#external-import').click()
                page.locator('#external-files').set_input_files({
                    'name': 'inventory.csv', 'mimeType': 'text/csv',
                    'buffer': b'ID,Label,Kind\na,Alpha,host\nb,Beta,switch\n'})
                page.locator('#external-file-choices select').select_option(',')
                with page.expect_response('**/api/import/inspect'):
                    page.locator('#external-inspect-files').click()
                page.locator('#external-add-view').click()
                view = page.locator('#external-views fieldset').first
                view.locator('input[placeholder^="Rubrikrad"]').fill('1')
                view.locator('input[placeholder^="Valda originalrader"]').fill('2,3')
                for field, column in (('node.id', 'A'), ('node.label', 'B'), ('node.kind', 'C')):
                    view.locator('label').filter(has_text=field).locator('input').fill(column)
                view.locator('input[placeholder^="Valda originalrader"]').dispatch_event('change')
                with page.expect_response('**/api/import/build-candidate'):
                    page.locator('#external-plan-button').click()
                choices = page.locator('#external-plan-result .unit-choice')
                expect(choices).to_have_count(2)
                for index in range(choices.count()):
                    choices.nth(index).check()
                with page.expect_response('**/api/import/build-candidate') as candidate:
                    page.locator('#external-candidate-button').click()
                assert candidate.value.json()['plan']['canApply']
                page.locator('#external-warning').check()
                with page.expect_response('**/api/import/build-candidate'):
                    page.locator('#external-apply').click()
                wait_layout(page)
                assert page.locator('#count-nodes').inner_text() == '2'
                assert not any(node.get('x') is None for node in candidate.value.json()['plan']['proposedProject']['nodes'])
                page.locator('#external-close').click()

                csv_files = [{'name': name+'.csv', 'mimeType': 'text/csv',
                              'buffer': data.encode()} for name, data in legacy.items()]
                page.evaluate("""() => {
                  window.__originalELK = window.ELK;
                  window.ELK = class extends window.__originalELK {
                    layout(graph) { return new Promise((resolve, reject) =>
                      setTimeout(() => super.layout(graph).then(resolve, reject), 900)); }
                  };
                }""")
                with page.expect_response('**/api/import/csv'):
                    page.locator('#import-file').set_input_files(csv_files)
                expect(page.locator('#layout-status')).to_contain_text('ELK beräknar')
                page.locator('#save-project').click()
                assert not (Path(directory)/'lab.yadilab').exists()
                page.locator('#new-project').click()
                page.wait_for_timeout(1200)
                assert page.locator('#count-nodes').inner_text() == '0'
                assert not (Path(directory)/'lab.yadilab').exists()

                with page.expect_response('**/api/import/csv'):
                    page.locator('#import-file').set_input_files(csv_files)
                expect(page.locator('#layout-status')).to_contain_text('ELK beräknar')
                page.locator('#saved-projects').select_option('auto-ods')
                page.locator('#open-project').click()
                page.wait_for_timeout(1200)
                assert page.locator('#count-nodes').inner_text() == '5'
                assert page.locator('#layout-controls').is_hidden()

                with page.expect_response('**/api/import/csv'):
                    page.locator('#import-file').set_input_files(csv_files)
                expect(page.locator('#layout-status')).to_contain_text('ELK beräknar')
                with page.expect_response('**/api/import/ods'):
                    page.locator('#import-file').set_input_files({
                        'name': 'latest.ods', 'mimeType': 'application/vnd.oasis.opendocument.spreadsheet',
                        'buffer': make_ods(rich)})
                wait_layout(page)
                page.wait_for_timeout(1200)
                assert page.locator('#count-nodes').inner_text() == '5'

                with page.expect_response('**/api/import/csv'):
                    page.locator('#import-file').set_input_files(csv_files)
                expect(page.locator('#layout-status')).to_contain_text('ELK beräknar')
                body = page.locator('g.network-node[data-node-id="pc-a"] rect.node-box')
                box = body.bounding_box()
                assert box is not None
                start = (box['x']+45, box['y']+25)
                page.mouse.move(*start)
                page.mouse.down()
                page.mouse.move(start[0]+55, start[1]+30, steps=5)
                page.mouse.up()
                moved = page.locator('g.network-node[data-node-id="pc-a"]').get_attribute('transform')
                page.wait_for_timeout(1200)
                assert page.locator('g.network-node[data-node-id="pc-a"]').get_attribute('transform') == moved
                assert not page.locator('#layout-status').inner_text().startswith('Automatisk ELK-layout klar.')

                # Worker failure leaves the imported reserve geometry and an
                # explicit error; the project still has no automatic Save.
                page.evaluate("""() => {
                  window.ELK = class extends window.__originalELK {
                    layout() { throw Error('test worker failure'); }
                  };
                }""")
                with page.expect_response('**/api/import/csv') as failed_layout_import:
                    page.locator('#import-file').set_input_files(csv_files)
                expected = failed_layout_import.value.json()['project']
                expect(page.locator('#layout-status')).to_contain_text(
                    'Automatisk ELK-layout misslyckades:')
                assert page.locator('#count-nodes').inner_text() == '2'
                page.locator('#project-filename').fill('reserve')
                page.locator('#project-filename').dispatch_event('change')
                assert not (Path(directory)/'reserve.yadilab').exists()
                page.locator('#save-project').click()
                expect(page.locator('#save-indicator')).to_contain_text('Sparat')
                assert store.read('reserve')['project'] == expected
                page.evaluate('() => { window.ELK = window.__originalELK; }')

                # Canceling the file prompt never creates a new candidate or
                # starts a layout for the current saved project.
                page.remove_listener('dialog', accept)
                page.once('dialog', lambda dialog: dialog.dismiss())
                page.locator('#import-file').set_input_files(csv_files)
                assert page.locator('#layout-status').inner_text().startswith(
                    'Automatisk ELK-layout misslyckades:')
                assert store.read('reserve')['project'] == expected
                page.on('dialog', accept)

                # A truly hung Worker reaches the production timeout, reports
                # failure and leaves the accepted import's reserve geometry.
                page.evaluate("""() => {
                  window.ELK = class extends window.__originalELK {
                    layout() { return new Promise(() => {}); }
                  };
                }""")
                with page.expect_response('**/api/import/csv') as timeout_import:
                    page.locator('#import-file').set_input_files(csv_files)
                expect(page.locator('#layout-status')).to_contain_text(
                    'Automatisk ELK-layout misslyckades:', timeout=55000)
                assert 'tidsgränsen' in page.locator('#layout-status').inner_text()
                assert not (Path(directory)/'lab.yadilab').exists()
                assert timeout_import.value.json()['project']['nodes'][0]['x'] == 110
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=4)
    print('PASS direct HTTP Chromium automatic ELK for CSV, XLSX, ODS and flexible import')


if __name__ == '__main__':
    run()
