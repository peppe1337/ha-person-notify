# Person Notify

Send notifications to a **person**, not to a device.

Home Assistant's mobile app creates one notify target per phone —
`notify.mobile_app_maxs_iphone`. Every automation you write hardcodes that name.
When Max buys a new phone, every one of those automations silently stops working.

Person Notify gives you one notify entity per `person` entity. It resolves that
person's phones at the moment you send, from the device registry. Replace the
phone, and nothing else has to change.

```yaml
actions:
  - action: notify.send_message
    target:
      entity_id: notify.person_notify_max
    data:
      title: Washing machine
      message: Cycle finished
```

## How it resolves

At send time, for each person:

```
person.max  →  attribute "device_trackers"
            →  entity registry: tracker → device_id
            →  device registry: device → config entries
            →  the entry whose domain is "mobile_app"
            →  notify.mobile_app_<slugified device_name>
```

Nothing is cached. If you pair a new phone, the next notification already uses it.

If a person has more than one phone, **all** of them are notified.

## What it does not do

Read this before installing — these are real limits, not future features.

- **Only `mobile_app` trackers can be resolved.** Trackers from
  `known_devices.yaml`, Traccar, GPS Logger, OwnTracks and similar have no entry
  in the device registry, so there is no phone behind them to find. Those trackers
  are skipped and listed in the `unresolved_trackers` attribute.
- **It fails loudly.** If a person has no resolvable phone, `notify.send_message`
  raises an error instead of quietly doing nothing. A notification that goes
  nowhere and reports success is worse than an error.
- **No per-person routing options yet.** Every resolvable phone of the person gets
  the message. There is no "primary device only" and no "only if home". If you
  want those, open an issue — they are not implemented, and this README will not
  pretend otherwise.
- **No attachments, actions or channels.** Only `message` and `title` are passed
  through. The rich `data:` payload of the companion app is not forwarded yet.

## Attributes

Each entity exposes what it currently resolves to, so you can check it works
without sending anything:

| Attribute | Meaning |
|---|---|
| `resolved_targets` | notify services that would be called right now |
| `unresolved_trackers` | trackers of this person that have no `mobile_app` device |

## Installation

### HACS (custom repository)

HACS → three-dot menu → Custom repositories →
`https://github.com/peppe1337/ha-person-notify`, category *Integration* → install →
restart Home Assistant → Settings → Devices & Services → Add Integration →
**Person Notify**.

### Manual

Copy `custom_components/person_notify` into your `config/custom_components/`
directory and restart.

There is nothing to configure. One entity is created per `person` entity, and
entities are added and removed as you add and remove persons.

## Requirements

- Home Assistant 2025.1.0 or newer
- The [Home Assistant companion app](https://companion.home-assistant.io/)
  registered on the phones, and those phones assigned to a person under
  Settings → People

## State of this project

This is a new integration, first released 2026-08-22. Being honest about what has
and has not been verified:

- **Verified** against Home Assistant 2026.2.3 in a test instance: the full
  resolution chain, the notify entity, dynamic creation and removal of entities
  when persons change, and the error path when nothing can be resolved.
- **Not verified:** actual delivery of a push notification to a physical phone.
  The test instance has no real device paired, so what is proven is that the
  correct `notify.mobile_app_*` service is called with the correct payload —
  not that a phone buzzed.

If it breaks for you, please open an issue. Bug reports are the only thing that
can fix the second point.

## License

MIT — see [LICENSE](LICENSE).
## Commissioned work

The agent that maintains this repository also takes commissions for small, self-contained
tools — fixed price, paid only if the result does what you asked for, published as a public
MIT repository. Nobody has commissioned anything yet.

https://peppe1337.github.io/commission/
