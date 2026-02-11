# Privacy Policy

**OneThing**
**Last updated:** February 2025

## Overview

OneThing is a daily focus tracker for iOS and Apple Watch. Your privacy is important to us. This policy explains what data the app handles and how it is stored.

## Data Collection

**OneThing does not collect, transmit, or share any personal data.** The app has no servers, no analytics, no third-party SDKs, and no advertising.

## Data Stored on Your Device

OneThing stores the following data locally on your device using UserDefaults and App Group shared storage:

- **Daily focus text** -- the focus you set each day
- **Focus history** -- past focuses with dates, completion status, and optional reflection notes
- **Gamification state** -- XP, level, streak count, and streak freeze inventory
- **App preferences** -- notification settings, animation intensity, haptics preference
- **Notification schedule** -- your chosen morning reminder and evening nudge times

This data never leaves your device unless you explicitly choose to export or share it.

## Apple Watch

If you use the Apple Watch companion app, your focus state is synced between your iPhone and Apple Watch using Apple's WatchConnectivity framework. This is a direct, local connection between your paired devices -- no data passes through external servers.

## Home Screen Widget

The Home Screen and watch face widgets read your focus state from shared on-device storage (App Group). No network requests are made.

## iCloud Sync

OneThing includes optional iCloud sync capability using Apple's iCloud key-value storage. When enabled, your focus history and gamification state sync across your devices through your personal iCloud account. This data is governed by [Apple's iCloud privacy policy](https://www.apple.com/legal/privacy/). No data is sent to any other server.

## Notifications

OneThing can send local notifications (morning reminder and evening nudge). These are scheduled entirely on your device. No push notification service or external server is involved.

## CSV Export

You can export your focus history as a CSV file. This file is generated locally and shared only through the iOS share sheet at your discretion. OneThing does not upload or transmit this file.

## Siri & Shortcuts

OneThing supports Siri Shortcuts for setting your focus and marking it complete. Voice processing is handled entirely by Apple's system. OneThing does not access or store any voice data.

## Third-Party Services

OneThing uses **no** third-party services, SDKs, analytics, crash reporting, or advertising frameworks.

## Children's Privacy

OneThing does not knowingly collect any information from children. The app stores no personal information and has no user accounts.

## Data Deletion

All app data can be deleted by removing the app from your device. Since no data is stored on external servers, deletion is immediate and complete.

## App Store Privacy Labels

In accordance with Apple's App Store requirements, OneThing declares:

- **Data Not Collected** -- OneThing does not collect any data from users

## Changes to This Policy

If this policy changes, the updated version will be included with the app and the "Last updated" date above will be revised.

## Contact

If you have questions about this privacy policy, please open an issue at:
[Apple's iCloud privacy policy](https://github.com/moonbeamalpha/OneThingPrivacyPolicy/issues)
