# Anki Haptics

Haptics device integration for Anki.

## WARNING

Test the add-on with your devices away from your body first to make sure they do not do anything unexpected. If you run into odd behavior, [report issues here](https://github.com/Kuuuube/ankihaptics/issues).

## Setup

1. Install [Intiface Central](https://intiface.com/central/)

2. Run Intiface Central and start the server by clicking on the top left start button (▶). (Optionally, enable `Start Server when Intiface Central Launches` in `App Modes`)

    For further information on setting up and connecting your device to Intiface Central, see the [official documentation](https://docs.intiface.com/docs/intiface-central/quickstart).

3. Install the Anki Haptics addon.

    - Open Anki.

    - On the top menu, go to `Tools` > `Add-ons`.

    - Click `Get Add-ons...`.

    - Input `247550864`

    - Click `OK`.

    - Restart Anki

4. Start Anki. If Anki was already started, go to `Tools` > `Anki Haptics Settings` and click `Reconnect`.

5. In `Tools` > `Anki Haptics Settings`, enable your device and configure your settings.

## Usage

Haptics activation are supported for the following Anki actions:

```
Again button press
Hard button press
Good button press
Easy button press
Show question
Show answer
```

All actions can be configured individually in settings.

## Settings Values

Save your settings before switching devices or closing the settings window. Settings are not saved automatically.

### General

- `Device Enabled` Whether or not the device should be sent commands such as vibration.

- `Enabled Pattern` Checks whether a command can be sent on the current card. `*` matches all cards. Uses the same format as [Anki's Browser Searching](https://docs.ankiweb.net/searching.html).

- `Actuators` These will show up as checkboxes such as `Vibrate`. Check or uncheck them to enable or disable triggering these features on your device.

    Only scalar device features are supported. This includes any feature that can be addressed by a single 0-100% value.

    - `Strength Multiplier` Multiplies strength when activating this actuator.

    - `Duration Multiplier` Multiplies duration when activating this actuator.

### Anki Actions

- `Again Button` Checks whether a command can be sent when pressing the again button.

    - `Strength` Strength to activate at when pressing the again button.

    - `Duration` Duration to activate for when pressing the again button.

- `Hard Button` Checks whether a command can be sent when pressing the hard button.

    - `Strength` Strength to activate at when pressing the hard button.

    - `Duration` Duration to activate for when pressing the hard button.

- `Good Button` Checks whether a command can be sent when pressing the good button.

    - `Strength` Strength to activate at when pressing the good button.

    - `Duration` Duration to activate for when pressing the good button.

- `Easy Button` Checks whether a command can be sent when pressing the easy button.

    - `Strength` Strength to activate at when pressing the easy button.

    - `Duration` Duration to activate for when pressing the easy button.

- `Show Question` Checks whether a command can be sent when showing a card.

    - `Strength` Strength to activate at when showing a card.

    - `Duration` Duration to activate for when showing a card.

- `Show Answer` Checks whether a command can be sent when flipping a card.

    - `Strength` Strength to activate at when flipping a card.

    - `Duration` Duration to activate for when flipping a card.

### Streaks

Streaks apply to all connected devices.

- `Streak Type`:

    `Per Collection` Streaks are calculated per-collection (all decks combined). Breaking a streak on one card breaks the streak for the entire collection.

    `Per Deck` Streaks are calculated per-deck. Breaking a streak on one card in a deck breaks the streak on the entire deck.

    `Per Card` Streaks are calculated per-card. Breaking a streak on one card does not mean streaks on all cards are broken.

- `Again Button` If unchecked, the again button breaks streaks. If checked, the again button adds to streaks.

    - `Strength` and `Duration` Multiplies strength and duration when pressing the again button in a streak.

- `Hard Button` If unchecked, the hard button breaks streaks. If checked, the hard button adds to streaks.

    - `Strength` and `Duration` Multiplies strength and duration when pressing the hard button in a streak.

- `Good Button` If unchecked, the good button breaks streaks. If checked, the good button adds to streaks.

    - `Strength` and `Duration` Multiplies strength and duration when pressing the good button in a streak.

- `Easy Button` If unchecked, the easy button breaks streaks. If checked, the easy button adds to streaks.

    - `Strength` and `Duration` Multiplies strength and duration when pressing the easy button in a streak.

- `Minimum Length` Minimum number of streak adding buttons to press for streak multipliers to activate.

- `Maximum Length` Streaks past this length will no longer increase the multiplier. The last highest multiplier stays in effect until the streak is broken.

- `Maximum Time` Maximum time to look back to find whether a streak is present for a card.

## Config Values

For advanced users only. Accessible through `Tools` > `Add-ons` > `Anki Haptics` > `Config`. Restarting Anki is recommended after changing config values.

The config can also be used to fine-tune settings values.

- `websocket_path` The websocket path configured in Intiface Central.

- `reconnect_delay` The delay in seconds to wait when reconnecting to Intiface central.

- `websocket_polling_delay_ms` The delay in milliseconds to wait before the websocket thread polls for commands again. Increases or decreases latency when actions occur.

    Increase this value if you notice Anki's CPU usage spikes after installing this add-on. But be careful increasing it too much as this will add to timer inaccuracies.

## Troubleshooting

### Scanning can't find device

Sometimes, requesting to scan for a device through Anki Haptics doesn't work.

Connect your device through scanning in Intiface directly instead and Anki Haptics will find it without needing to scan.

(You may need to restart Intiface if it has already failed once through Anki Haptics)

### Something broke!

First, try restarting Anki and see if that fixes it.

Second, reset your settings to default (`Tools` > `Add-ons` > `Anki Haptics` > `Config` > `Restore Defaults`) and restart Anki.

If neither of those helped, please [report an issue here](https://github.com/Kuuuube/ankihaptics/issues).

## Info

[Github Repository](https://github.com/Kuuuube/ankihaptics)

[Report Issues Here](https://github.com/Kuuuube/ankihaptics/issues)
