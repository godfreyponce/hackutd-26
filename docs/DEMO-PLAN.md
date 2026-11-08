# LAND judge demo: run of show (agreed 2026-11-08)

Rafael's plan, written up for the team. The box is **wall mounted** for the demo. The judges watch the
**demo page on a laptop** (`deploy/laptop/LAND-demo.cmd`, over Wi-Fi, no HDMI). The Pi's own screen shows the
home kiosk. About 4 minutes, then questions on the dashboard (map, affected area, LAND-to-LAND).

## Run of show

| Time | On stage | What the box does | Status |
|---|---|---|---|
| 0:00 | Rafael turns on **live radio** | NOAA Weather Radio 162.400 MHz, live off our antenna, plays on the box speaker | built (`radio_live`, `hardware/radio/tap.py`) |
| 0:10 | "Do y'all hear that?" Rafael presses **Emergency broadcast** | Live audio stops. The EQW alert recording plays **on the box speaker** and goes into the real SAME decoder at broadcast speed. Decoded header on screen, ring + screens red. Box: "DEMO, not a real alert." then "Something just happened. Are you okay?" (does not say what happened) | built (`radio_eqw`); the recording is made fresh so its issue time is now |
| 0:40 | "We're okay." Then ask: what happened, where, when, what do we do | Answers from the decoded alert (event, area, issued, expires, sender) + the safety sheet (`hardware/demo/safety_guide.md`). Cloud Nemotron online, on-board Nemotron 3 Nano 4B offline. Rocky-style talk for answers only | built |
| 1:10 | Rafael **shakes the box**, Godfrey acts out the quake and explains the ring | Ring = red bar, LEDs lit = shaking strength (16 LEDs = 1.2 g). When the shaking **stops**: "Something just happened. Are you okay?" | built (`shake` events, quake sent when shaking stops) |
| 1:40 | Godfrey lies on the floor | Camera (judges see it): LYING. Asks 3 times. Then alarm: "I haven't heard back, so I'm alerting your emergency contact now." Twilio call to the team phone | built; Twilio needs the env vars |
| 2:40 | Godfrey **stands up** | Cancels: "I see you're up. Are you okay, and can you talk? If you can't talk, put a hand on your head for okay, or cross your arms over your head for help." | built |
| 2:50 | Godfrey shows **X** (or says help) | "Okay. I hear you. Stay with me, you're not alone." then "Do you want me to call emergency services? I'll put the call on my speaker so you can talk." | built |
| 3:00 | "Yes" (or X, or silence) | "Calling now. Stay with me." Phone rings (a teammate's phone stands in for 911; **never 911**). LAND speaks first, 1-2 sentences of what it saw, then "Handing the call to the homeowner." Chime, then two-way audio with live transcript on the demo page | one-way call built (LAND reads the summary); **two-way bridge: Godfrey, see issue** |
| 3:40 | Close | "Power outage": battery, internet cut, every AI part moves on-board; ask one more question offline | built |

If "okay" instead: "Good, I'm glad you're okay. I'm here if you need me, and you can call 911 anytime."

## Hand signs (camera, front view, hold 3 s)

Pose keypoints have no fingers, so both signs use the arms.

- **O = okay**: one hand on top of the head, or the other hand, or both (3 ways). Elbow raised.
- **X = help / not okay**: both forearms crossed over the head. Needs two hands.
- Held 3 s before the box acts. The demo page and camera overlay show the countdown.
- Answers the open question exactly like speaking: O = ok, X = help. An X with no question open starts a check-in.
- Speaking works the same as always ("okay", "help me", "I'm not okay", ...).

## Spoken lines (new or changed today, review: Godfrey + Rafael)

| id | line |
|---|---|
| `standup_ask` | I see you're up. Are you okay, and can you talk? If you can't talk, put a hand on your head for okay, or cross your arms over your head for help. |
| `reply_ok` | Good, I'm glad you're okay. I'm here if you need me, and you can call 911 anytime. |
| `reply_help` | Okay. I hear you. Stay with me, you're not alone. |
| `offer_call` | Do you want me to call emergency services? I'll put the call on my speaker so you can talk. |
| `call_now` | Calling now. Stay with me. |
| `call_declined` | Okay, no call. I'm right here. Say help anytime. |
| call opening (on the phone) | This is LAND, a home safety box, calling for the person at home. {what it saw}. They are now up and asking for help. Handing the call to the homeowner. |

Unchanged: `ask_event`, `ask_retry_2`, `ask_retry_3`, `escalate`, `alert_demo`.

## The alert audio

The SAME recording plays on the box speaker in the room. It is never transmitted: transmitting EAS tones is what
47 CFR 11.45 bans, and an antenna cannot pick up a phone speaker anyway (it hears 162.4 MHz radio waves, not
sound). Station HACKDEMO marks it as ours, so the box always says "DEMO, not a real alert".

## For the judges' questions

**Calling without Wi-Fi.** A cellular modem board on the Pi (for example a SIM7600 4G HAT) is the radio part of a
phone without the screen: it talks to the nearest cell tower over the carrier's licensed bands (roughly 600 MHz to
2.5 GHz in the US) and does real voice calls, texts and data with a SIM card. Towers run on backup power, so it
works when the house has no power or internet. A real product would call a 24/7 monitoring center that sends 911
with the home address (how medical-alert devices work). When towers are down too, a satellite modem (Iridium) can
still send short text messages. We do not have this hardware.

**LAND to LAND.** The Pi 5 has Wi-Fi and Bluetooth; the RTL-SDR only receives. Over the internet: works today
through the hub. With no internet: LoRa radios (915 MHz, license-free, kilometers of range, Meshtastic) would form a
neighborhood mesh; not bought. Early warning: messages travel near light speed, quake shaking about 3.5 km/s, so a
box near the start can warn boxes 35 km away roughly 5-10 s early (the ShakeAlert / MyShake idea). Several boxes
must agree before a city-wide warning, so one bumped table cannot set it off.

## Owners

- Rafael (with Claude): radio live + alert playback, hand signs, shake ring, safety sheet, Rocky-style text,
  call offer flow, demo page, offline mode, Pi deploy.
- Godfrey: live two-way call bridge (issue), the Rocky-style ElevenLabs voice (`ELEVEN_ASSISTANT_VOICE_ID`, issue),
  review of the lines above.
