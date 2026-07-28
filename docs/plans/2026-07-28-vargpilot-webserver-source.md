# VargPilot webserver source — removed, and how to bring it back

**Status:** removed from the app on 2026-07-28. This document is the complete
record needed to restore it. Live code is in git history: the commit that
removed it, and everything before it (search `vpConnect`).

## What it was

DingoNav had **two** telemetry sources for the Stark Varg, chosen by a
`Source` segmented control in Settings → Stark:

| Source | How it got data |
|---|---|
| **VargPilot** (`vargSrc: 'vp'`) | WebSocket to VargPilot's built-in BikeStore webserver, which holds the bike's BLE link and re-serves fully-decoded telemetry |
| **Direct BLE** (`vargSrc: 'ble'`) | Web Bluetooth straight to the VCU |

VargPilot was the *preferred* source when it was written (2026-07-14): direct
BLE was unproven, and VP had already done the decoding work.

## Why it was removed

Direct BLE now works on the real bike (battery, speed, ride mode, blinkers,
neutral, reverse/crawl, alerts — confirmed 2026-07-28 on Grant's '25 EX), and
maintaining two sources meant every feature and every status string had two
code paths. The VP path also required the rider to find VP's LAN URL and keep
both devices on the same Wi-Fi, which is fragile at a trailhead.

**Note the subtlety:** removing the VP *webserver source* does **not** stop
DingoNav from working with the VargPilot *app*. Direct BLE piggybacks on
VargPilot's BLE connection — the VCU only streams once VP (or the stock Stark
app) has started the telemetry. VP the app is still part of the working
setup; only its WebSocket source is gone.

## What was lost

1. **hp / regen / TC per-mode values.** These are per-map *configuration*, not
   telemetry — they have no known BLE characteristic (and no field in
   `svag-telemetry-format`'s `v1.proto`). Only VP served them. The telemetry
   page now labels them "VP only". Recovering them over BLE means identifying
   the unmapped characteristics (see the "Probe extra channels" button).
2. **Automatic VIN + pair-PIN capture** (`vpSniff`). VP's catalog contained
   both, so connecting to VP once pre-configured Direct BLE. Now the rider
   types the VIN (and reads the PIN from VP's own UI) once.
3. **iOS support.** Web Bluetooth is Chrome/Android-only; the VP WebSocket
   worked in any browser. **If iOS support is ever needed, restoring this is
   the way** — that is the single strongest reason to bring it back.

## Protocol (confirmed against live VP 0.1.125, 2026-07)

One WebSocket at `<base>/ws`:

1. Server greets with `{op:'hello'}`
2. Server sends `{op:'catalog', paths:[{path, writable}, …]}`
3. Client sends `{op:'sub', paths:[…]}`
4. Server sends `{op:'prop', path, value, t}` per update
5. Server pings every 15 s (browsers auto-pong — nothing to implement)

Paths are dot-hierarchical. Subscribing is what marks the client live.

### Path map (verified live on a '25 EX, 2026-07)

```js
const VP_P = {
  soc:  'Battery.SOC.soc_pct',
  soh:  'Battery.SOC.soh_pct',
  vbus: 'Battery.SOC.dc_bus_v',
  mode: 'Live.MAPS.riding_map',
  // ground truth for the reverse/crawl takeover: a human-readable string —
  // "NEUTRAL" / "DRIVE" / "CRAWL REV" (reverse) / "CRAWL FWD" (crawl).
  drive: 'derived.power.drive_state',
  walk:  'Bike.STATUS_BITS.misc_bits.walking_mode', // fallback: 8 = rev, 12 = crawl
  blinkerL: 'Bike.STATUS_BITS.indicator_bits.blinker_left',  // toggles ~3 Hz with the bulb
  blinkerR: 'Bike.STATUS_BITS.indicator_bits.blinker_right',
  beam:     'Bike.STATUS_BITS.indicator_bits.beam_long',     // steady while high beam on
};

// per-mode config: "torque" is the power (hp) slider on the EX
const vpMapPaths = m => [
  ['Vcu.BIKE_CONFIG.MAP.' + m + '.torque', 'hp',    m],
  ['Vcu.BIKE_CONFIG.MAP.' + m + '.regen',  'regen', m],
  ['derived.tc.' + m + '.power_tc',        'tc',    m],
];
```

These same `STATUS_BITS` words are what the BLE status characteristic
(`00001002`) carries — VP just decodes them for you. The `walking_mode`
values 8 = reverse and 12 = crawl were **confirmed on the bike through VP**,
and that is where the BLE decoder's values came from.

### Decode notes worth keeping

- `drive_state` is authoritative for reverse/crawl/neutral; `walking_mode` was
  only a fallback for when `drive_state` never arrived (`vp.sawDrive` flag).
- Blinker paths pulse true/false at ~3 Hz with the bulb. Only the `true`
  pulses matter — feed them to `vargBlink(side)`, whose watchdog
  (`BLINK_OFF_MS` 700 ms) collapses them into a steady telltale. That
  debounce logic is still in the app; the BLE status decoder uses it.
- URL normalising: prepend `http://` if absent, strip trailing slashes, then
  swap `http` → `ws` for the socket (`vpUrlBase()`).
- Reconnect was a flat 3 s retry on `onclose`.

## To re-enable

1. Restore the `S.set` keys: `vargSrc: 'vp'` (source selector) and
   `vpUrl: ''`.
2. Restore the settings registry rows — the `Source` segmented control
   (`opts: [['vp','VargPilot'], ['ble','Direct BLE']]`, `apply: applyVarg`)
   and the `vpUrl` text row (`sec: 'vp'`, placeholder
   `http://127.0.0.1:8080`).
3. Restore the settings markup: the `VargPilot server` heading, its
   `data-reg="vp"` mount, and the `#vpRow` button row (Connect +
   `Probe API → console`).
4. Restore `vp`, `VP_P`, `vpMapPaths`, `vpUrlBase`, `vpClose`, `vpConnect`,
   `vpSniff`, `vpProp`, `vpApplyMode`, `vpProbe`.
5. Re-add the source branches: `vargUI` (row visibility + VP status strings),
   `applyVarg` (`vpConnect` vs `vargBoot`), the telemetry page's source cell
   and Reconnect handler, and the `vargSrc === 'ble'` guards in
   `vargDropped` / `vargRetry` / `vargEnsure` / the stale-stream watchdog.

Everything decoded from VP fed the same `vargApplyState({mode, special,
neutral, hp, regen, tc})` entry point the BLE decoders use, so the UI layer
needs no changes — only the source plumbing.

## Related

- `docs/varg-ble.html` — the BLE protocol spec (rev 2) for the direct path.
- The mock VP server used for testing was a small dependency-free Node script
  with a raw WebSocket handshake, kept in a scratchpad; rebuild if needed.
