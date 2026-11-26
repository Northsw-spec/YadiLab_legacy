import {$, el} from '../../ui/dom.js';

// Renders one ICMP panel from the canonical project and a copied session view.
function icmpInvestigationDescription(item) {
  if (item.error) return 'MÄTNING AVVISAD: ' + item.error;
  const o = item.observation;
  if (item.probe === 'address') {
    return 'IP/KLient: dokumenterad ' + o.documentedIpv4
      + ' · gränssnitt ' + (o.interfaceEnabled ? 'aktiverat' : 'avstängt')
      + '\nDHCP-ursprung: ' + o.origin + ' · kontroll: ' + o.dhcpStatus
      + '\n' + o.reason;
  }
  if (item.probe === 'route') {
    const formatStatic = (id, destination, nextHop, outPort) =>
      (id ? id + ' · ' : '') + destination + ' via ' + nextHop + ' ut ' + outPort;
    const documented = o.documentedStaticRoutes.map(r =>
      formatStatic(r.id, r.destination, r.nextHop, r.outPort));
    const simulated = o.routes.filter(r => r.type === 'STATIC').map(r =>
      formatStatic(r.routeId, r.destination, r.nextHop, r.outInterface.port));
    return 'ROUTING (' + o.sourceNode + ' → ' + o.destinationIpv4 + '): ' + o.status
      + '\nVald route: ' + (o.selectedRoute
        ? o.selectedRoute.destination + ' via '
          + (o.selectedRoute.nextHop ?? 'CONNECTED')
          + ' ut ' + o.selectedRoute.outInterface.port : 'ingen entydig matchning')
      + '\nDokumenterade statiska routes: '
      + (documented.join(' | ') || 'inga')
      + '\nSimulerade aktiva statiska routes: '
      + (simulated.join(' | ') || 'inga')
      + '\nEn route-matchning bevisar inte ARP-svar eller ping.';
  }
  if (item.probe === 'ping') {
    const hops = [...o.requestSteps.map(step => ({direction:'UT', ...step})),
                  ...o.replySteps.map(step => ({direction:'RETUR', ...step}))];
    const error = o.routerError;
    const errorType = error?.type === 11 && error?.code === 0
      ? 'Time Exceeded – TTL expired in transit'
      : error?.type === 3 && error?.code === 0
        ? 'Destination Unreachable – Network Unreachable'
        : 'okänd eller ej stödd typ/kod';
    const routerEvidence = error
      ? '\nRouter-ICMP i simuleringen: typ ' + error.type + '/kod ' + error.code
        + ' (' + errorType + ') från ' + error.sourceNode + '/' + error.sourcePort
        + ' · citerad destination ' + error.quotedDestinationIpv4
        + (error.receivedAtSource
          ? ' · MOTTAGET vid ursprungskällan i modellen'
          : ' · INTE MOTTAGET vid ursprungskällan; generering i modellen är inte en observerad felrespons')
        + ' · returspår ' + error.returnTraceStatus
      : '\nRouter-ICMP: inget genererat av denna begränsade modell i försöket; '
        + 'ett saknat Echo Reply bevisar inte att en router skickade ett fel.';
    return 'ICMP: ' + o.status + ' · giltig Echo Reply: ' + (o.replyMatched ? 'ja' : 'nej')
      + '\nEcho Request: ' + o.requestStatus + ' · Echo Reply: ' + (o.replyStatus ?? 'ej skickad')
      + routerEvidence
      + '\n' + (hops.map(step => step.direction + ' · ' + step.node
        + ' · route ' + step.route.type + ' ' + step.route.destination
        + ' · ARP ' + step.arpStatus
        + ' · nästa hopp ' + step.nextHopIpv4
        + ' · kablar ' + (step.transmissions.map(t => t.linkId).join(', ') || 'inga')
        + ' · VLAN-drops ' + step.vlanDrops.length).join('\n') || 'Ingen paketväg nådd');
  }
  if (item.probe === 'link') {
    return 'KABEL ' + o.linkId + ': dokumenterat ' + (o.documentedEnabled ? 'UP' : 'DOWN')
      + ' · i aktuell simulering ' + (o.observedEnabled ? 'UP' : 'DOWN')
      + '\n' + o.endpoints.map(p => p.node + '/' + p.port).join(' ↔ ');
  }
  if (item.probe === 'port') {
    return 'PORT ' + o.nodeId + '/' + o.portId
      + ': dokumenterat admin ' + (o.documentedEnabled ? 'UP' : 'DOWN')
      + ' · simulerat admin ' + (o.observedEnabled ? 'UP' : 'DOWN')
      + '\nIPv4/CIDR dokumenterat: ' + (o.documentedIpv4 ?? 'ej konfigurerat')
      + ' · simulerat: ' + (o.observedIpv4 ?? 'ej konfigurerat');
  }
  if (item.probe === 'vlan') {
    return 'SWITCH VLAN ' + o.nodeId + '/' + o.portId
      + '\nDokumenterat: ' + JSON.stringify(o.documentedVlan)
      + '\nSimulerat: ' + JSON.stringify(o.observedVlan);
  }
  return JSON.stringify(o);
}

function renderLesson(session) {
  const panel = $('icmp-lesson');
  const opening = session.state?.openingObservation;
  const lessonId = opening ? session.id : '';
  if ((panel.dataset.sessionId ?? '') !== lessonId) {
    panel.dataset.sessionId = lessonId;
    delete panel.dataset.reviewed;
    $('icmp-lesson-reason').value = '';
    for (const choice of panel.querySelectorAll('input[type="radio"]')) {
      choice.checked = false;
    }
    if (opening) $('icmp-investigation-diagnosis').selectedIndex = -1;
  }
  const plan = session.lessonPlan;
  const reviewed = panel.dataset.reviewed === 'true';
  const measured = reviewed && session.state?.canDiagnose;
  const diagnosed = measured && session.verdict?.correct;
  const recovery = session.recovery;
  const verified = diagnosed && recovery?.status === 'RECOVERED' && recovery.verification;
  const endpoint = value => value.node + '/' + value.port;
  panel.hidden = !opening;
  $('icmp-lesson-symptom').textContent = opening
    ? 'Källan fick inget giltigt Echo Reply vid övningsstart (' + opening.source + ').'
    : '';
  const selectedHypothesis = panel.querySelector('input[name="icmp-lesson-hypothesis"]:checked');
  const selectedTest = panel.querySelector('input[name="icmp-lesson-test"]:checked');
  $('icmp-lesson-review').disabled = !opening || Boolean(plan)
    || !selectedHypothesis || !selectedTest;
  $('icmp-lesson-review').hidden = reviewed;
  for (const input of panel.querySelectorAll('input[name="icmp-lesson-hypothesis"], input[name="icmp-lesson-test"]')) {
    input.disabled = Boolean(plan);
  }
  $('icmp-lesson-reason').readOnly = Boolean(plan);
  const hypothesisText = {
    route: 'Saknad aktiv returroute',
    arp: 'Returroute finns men ARP-svar saknas',
    ipv4: 'Fel på IPv4-adress eller nätmask',
  };
  const testText = {
    route: 'Returrouteuppslag från b till källan',
    ping: 'Upprepat ICMP Echo',
    port: 'Kontroll av b/eth0',
  };
  const measuredTest = plan && session.log.some(item => {
    if (item.error || item.probe !== plan.diagnosticTest) return false;
    if (plan.diagnosticTest === 'route') {
      return item.observation?.sourceNode === 'b'
        && item.observation?.destinationIpv4 === session.state?.sourceIpv4;
    }
    if (plan.diagnosticTest === 'port') {
      return item.observation?.nodeId === 'b' && item.observation?.portId === 'eth0';
    }
    return true;
  });
  $('icmp-lesson-plan').textContent = plan
    ? 'Elevens hypotes (inte fastställd): ' + hypothesisText[plan.hypothesis]
      + '. Vald första mätning: ' + testText[plan.diagnosticTest]
      + '. Motbevisande observation (elevanteckning): '
      + (plan.counterEvidence || 'inte angiven')
      + '. Mätstatus: ' + (measuredTest ? 'utförd i simuleringen' : 'inte utförd')
      + '. Valet är ingen automatisk diagnos.'
    : '';
  $('icmp-lesson-measurements').hidden = !reviewed;
  $('icmp-lesson-interpretation').hidden = !measured;
  $('icmp-lesson-action').hidden = !diagnosed;
  const restoredRoute = verified && recovery.repair.expectedRoute;
  $('icmp-lesson-action-text').textContent = verified
    ? recovery.report.rootCause + ' ' + recovery.report.action
      + (restoredRoute
        ? ' På ' + recovery.repair.nodeId + ' återställdes ' + restoredRoute.destination
          + ' via ' + restoredRoute.nextHop + ' på ' + restoredRoute.outPort + '.'
        : '')
      + ' Åtgärden gäller bara den tillfälliga övningen.'
    : diagnosed ? 'Diagnosen stöds av mätningarna. Välj återställning för att verifiera den med ett nytt Echo-utbyte.' : '';
  $('icmp-lesson-verification').hidden = !verified;
  $('icmp-lesson-verification-text').textContent = verified
    ? 'Baslinje: ' + recovery.verification.baselineStatus + '. Med felet: '
      + recovery.failedEchoStatus + '. Efter återställning: ' + recovery.restoredEchoStatus
      + '. Request nådde ' + endpoint(recovery.verification.requestReceiver)
      + ' (' + recovery.verification.destinationIpv4 + '). Matchande Reply kom tillbaka till '
      + endpoint(recovery.verification.replyReceiver) + ' (' + recovery.verification.sourceIpv4 + '). '
      + recovery.report.evidence
    : '';
  return Boolean(opening && !reviewed);
}

export function renderIcmpInvestigationPanel(project, session) {
  const {id: icmpInvestigationId, state: icmpInvestigationState,
    busy: icmpInvestigationBusy, log: icmpInvestigationLog,
    verdict: icmpInvestigationVerdict, recovery: icmpInvestigationRecovery,
    error: icmpInvestigationError} = session;
  const active = icmpInvestigationId !== null;
  const busy = icmpInvestigationBusy;
  const lesson = Boolean(icmpInvestigationState?.lesson);
  const beforeMeasurements = renderLesson(session);
  $('icmp-lesson-start').disabled = active || busy || !project.nodes.length;
  $('icmp-lesson-case').disabled = active || busy;
  const diagnosis = $('icmp-investigation-diagnosis');
  const lessonDiagnoses = ['STATIC_ROUTE_MISSING', 'IPV4_PREFIX_MISMATCH',
    'IPV4_HOST_ADDRESS_MISMATCH', 'STATIC_NEXT_HOP_UNREACHABLE'];
  for (const option of diagnosis.options) {
    option.hidden = lesson && !lessonDiagnoses.includes(option.value);
  }
  if (!lesson && !diagnosis.value) diagnosis.selectedIndex = 0;
  const sourceSelector = $('icmp-investigation-source');
  const previousSource = sourceSelector.value;
  const sources = project.nodes.filter(n => n.kind !== 'switch').flatMap(n =>
    n.ports.filter(p => p.enabled && p.ipv4 !== null && p.mac !== null)
      .map(p => ({value: JSON.stringify([n.id,p.id]),
                  title: n.id + '/' + p.id + ' · ' + p.ipv4})));
  sourceSelector.replaceChildren(...sources.map(x => el('option', {value: x.value}, x.title)));
  if (sources.some(x => x.value === previousSource)) sourceSelector.value = previousSource;
  const linkSelector = $('icmp-investigation-link');
  const previousLink = linkSelector.value;
  const links = project.links;
  linkSelector.replaceChildren(...links.map(link => el('option', {value:link.id},
    link.id + ' · ' + link.a.node + '/' + link.a.port
    + ' ↔ ' + link.b.node + '/' + link.b.port)));
  if (links.some(x => x.id === previousLink)) linkSelector.value = previousLink;
  const routeSelector = $('icmp-investigation-route-node');
  const previousRoute = routeSelector.value;
  const nodes = project.nodes.filter(n => n.kind !== 'switch');
  routeSelector.replaceChildren(...nodes.map(n =>
    el('option', {value:n.id}, n.id + ' · ' + n.kind)));
  if (nodes.some(n => n.id === previousRoute)) routeSelector.value = previousRoute;
  const portSelector = $('icmp-investigation-port');
  const previousPort = portSelector.value;
  const ports = project.nodes.flatMap(n => n.ports.map(p => ({
    value: JSON.stringify([n.id,p.id]), title:n.id + '/' + p.id,
  })));
  portSelector.replaceChildren(...ports.map(p =>
    el('option', {value:p.value}, p.title)));
  if (ports.some(p => p.value === previousPort)) portSelector.value = previousPort;
  const vlanSelector = $('icmp-investigation-vlan');
  const previousVlan = vlanSelector.value;
  const vlans = project.nodes.filter(n => n.kind === 'switch').flatMap(n =>
    n.ports.filter(p => p.vlan !== null).map(p => ({
      value: JSON.stringify([n.id,p.id]), title:n.id + '/' + p.id,
    })));
  vlanSelector.replaceChildren(...vlans.map(v =>
    el('option', {value:v.value}, v.title)));
  if (vlans.some(v => v.value === previousVlan)) vlanSelector.value = previousVlan;

  const kind = $('icmp-investigation-probe').value;
  $('icmp-investigation-source').disabled = active || busy || !sources.length;
  $('icmp-investigation-destination').disabled = active || busy;
  $('icmp-investigation-ttl').disabled = active || busy;
  $('icmp-investigation-probe').disabled = !active || busy || beforeMeasurements;
  $('icmp-investigation-route-node').disabled = !active || busy || beforeMeasurements || kind !== 'route';
  $('icmp-investigation-route-destination').disabled = !active || busy || beforeMeasurements || kind !== 'route';
  $('icmp-investigation-link').disabled = !active || busy || beforeMeasurements || kind !== 'link';
  $('icmp-investigation-port').disabled = !active || busy || beforeMeasurements || kind !== 'port';
  $('icmp-investigation-vlan').disabled = !active || busy || beforeMeasurements || kind !== 'vlan';
  $('icmp-investigation-start').disabled = active || busy || !sourceSelector.value
    || !$('icmp-investigation-destination').value.trim();
  $('icmp-investigation-stop').disabled = !active;
  $('icmp-investigation-measure').disabled = !active || busy || beforeMeasurements
    || icmpInvestigationState?.observations >= icmpInvestigationState?.maxProbes
    || icmpInvestigationState?.repaired
    || (kind === 'link' && !linkSelector.value)
    || (kind === 'port' && !portSelector.value)
    || (kind === 'vlan' && !vlanSelector.value)
    || (kind === 'route' && !routeSelector.value);
  diagnosis.disabled = !active || busy || beforeMeasurements
    || Boolean(icmpInvestigationState?.diagnosed);
  $('icmp-investigation-diagnose').disabled = !active || busy || beforeMeasurements
    || (lesson && !lessonDiagnoses.includes(diagnosis.value))
    || Boolean(icmpInvestigationState?.diagnosed)
    || Boolean(icmpInvestigationState?.repaired)
    || !icmpInvestigationState?.canSubmitDiagnosis;
  $('icmp-investigation-repair').disabled = !active || busy
    || !icmpInvestigationState?.diagnosed || Boolean(icmpInvestigationState?.repaired)
    || !icmpInvestigationVerdict?.correct;

  $('icmp-investigation-status').textContent = busy
    ? 'ICMP-felsökning pågår…'
    : icmpInvestigationError ? 'ICMP-labb: ' + icmpInvestigationError
    : active
      ? (lesson ? 'Guidad Om–Då-övning · ' : 'Aktiv dold övning · ') + icmpInvestigationState.sourceNode
        + '/' + icmpInvestigationState.sourcePort
        + ' → ' + icmpInvestigationState.destinationIpv4
        + ' · ' + icmpInvestigationState.observations + ' mätningar'
        + (icmpInvestigationState.observations >= icmpInvestigationState.maxProbes
          ? ' · ' + icmpInvestigationState.observations + ' av '
            + icmpInvestigationState.maxProbes
            + ' mätningar använda – inga fler mätningar kan göras'
          : '')
        + (lesson ? '' : ' · DHCP-ursprung: ' + icmpInvestigationState.dhcpAddressOrigin
            + ' · DHCP-kontroll: ' + icmpInvestigationState.dhcpCheck)
        + (!icmpInvestigationState.diagnosed
            && icmpInvestigationState.diagnosisAttempts >= icmpInvestigationState.maxDiagnosisAttempts
          ? ' · ' + icmpInvestigationState.diagnosisAttempts + ' av '
            + icmpInvestigationState.maxDiagnosisAttempts
            + ' diagnosförsök förbrukade – avsluta och starta ny övning'
          : '')
      : 'Ingen ICMP-övning startad. En fungerande ICMP-baslinje krävs.';
  const observations = $('icmp-investigation-observations');
  observations.textContent = icmpInvestigationLog.length
    ? icmpInvestigationLog.map((x, i) =>
      (i + 1) + '. ' + icmpInvestigationDescription(x)).join('\n\n')
    : 'Börja med IP-uppgifter. Skicka sedan simulerat ICMP Echo och kontrollera routingtabeller '
      + 'samt länk, port/IPv4 och VLAN för att utesluta fel. DHCP-ursprung är okänt i modellen.';
  const verdict = $('icmp-investigation-verdict');
  verdict.classList.remove('ok', 'fail');
  if (icmpInvestigationVerdict?.error) {
    verdict.classList.add('fail');
    verdict.textContent = 'Diagnos avvisad: ' + icmpInvestigationVerdict.error;
  } else if (icmpInvestigationVerdict) {
    verdict.classList.add(icmpInvestigationVerdict.correct ? 'ok' : 'fail');
    verdict.textContent = icmpInvestigationVerdict.correct
      ? 'DIAGNOS BEKRÄFTAD. Återställ och verifiera ett matchande Echo Reply i simuleringen.'
      : 'HYPOTES AVVISAD. Felkategorin avslöjas inte; kontrollera flera mätningar.';
  } else {
    verdict.textContent = lesson
      ? 'För diagnos behövs ICMP Echo, uppslag från b mot källan och kontroll av b/eth0.'
      : 'Följ den riktning där Echo-utbytet misslyckas. Gör ett routeuppslag i den riktningen och jämför '
        + 'dokumenterat och simulerat tillstånd för relevant route, kabel, port eller VLAN.';
  }
  const recovery = $('icmp-investigation-recovery');
  recovery.classList.remove('ok', 'fail');
  if (icmpInvestigationRecovery?.error) {
    recovery.classList.add('fail');
    recovery.textContent = 'Reparation avvisad: ' + icmpInvestigationRecovery.error;
  } else if (icmpInvestigationRecovery) {
    recovery.classList.add(icmpInvestigationRecovery.status === 'RECOVERED' ? 'ok' : 'fail');
    recovery.textContent = 'RESULTAT: ' + icmpInvestigationRecovery.status
      + '\nFöre: ' + icmpInvestigationRecovery.failedEchoStatus
      + '\nEfter återställning: ' + icmpInvestigationRecovery.restoredEchoStatus
      + '\nGiltigt ICMP Echo Reply: ' + (icmpInvestigationRecovery.replyMatched ? 'ja' : 'nej')
      + (icmpInvestigationRecovery.status === 'RECOVERED' && lesson ? ''
        : icmpInvestigationRecovery.status === 'RECOVERED'
        ? '\n\nFELSÖKNINGSRAPPORT'
          + '\nSymptom: ' + icmpInvestigationRecovery.report.symptom
          + '\nRotorsak: ' + icmpInvestigationRecovery.report.rootCause
          + '\nTeknisk evidens: ' + icmpInvestigationRecovery.report.evidence
          + '\nÅtgärd: ' + icmpInvestigationRecovery.report.action
          + '\nVerifiering: ' + icmpInvestigationRecovery.report.verification
        : '\nReparationen är inte verifierad; inga positiva slutsatser får dras.');
  } else {
    recovery.textContent = 'Ingen reparation eller tvåvägskommunikation har verifierats.';
  }
}

