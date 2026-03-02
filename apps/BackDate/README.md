# Privacy Policy

**BackDate**
Last updated: March 2, 2026

---

## Overview

BackDate is designed with privacy as a core principle. Your goals and milestones are stored on your device and, optionally, in your own iCloud account. BackDate does not have its own servers, does not collect analytics, and does not share your data with third parties.

---

## Information We Collect

### Information You Provide

When you use BackDate, you create goals and milestone steps. This includes:

- Goal titles and descriptions
- Target dates and deadlines
- Step titles and completion status
- Notes and context you add to steps

This information is stored **locally on your device** using Apple's SwiftData framework.

### Automatically Collected Information

BackDate stores app preferences in your device's local storage (UserDefaults), including:

- App appearance setting (dark, light, or system)
- Notification preferences (times, lead times, digest day)
- Text size preference
- Whether onboarding has been completed

No usage data, crash reports, or analytics are collected or transmitted.

---

## How Your Information Is Used

Your data is used solely to provide the features of BackDate:

- Displaying your goals and milestone timeline
- Scheduling local reminder notifications
- Powering the home screen widget and Apple Watch complication
- Generating calendar events or .ics export files when you request them

---

## Optional Integrations

All integrations below are **opt-in** and require your explicit permission. You can revoke access at any time in iOS Settings.

### iCloud Sync

If you enable iCloud Sync in BackDate's settings, your goals and milestones are synced through **your own iCloud account** using Apple's CloudKit framework. This data is governed by [Apple's iCloud Privacy Policy](https://www.apple.com/legal/privacy/). BackDate does not have access to your iCloud data — the sync occurs directly between your devices.

You can disable iCloud Sync at any time in BackDate's settings, or manage iCloud data in iOS Settings → Apple ID → iCloud.

### Calendar Access

If you use the Calendar Sync feature, BackDate requests access to your Apple Calendar via EventKit. With your permission, it:

- Creates and updates all-day calendar events for your milestone steps
- Reads date changes from those events back into BackDate

BackDate only accesses events it has created (identified by a "Managed by BackDate" note). It does not read or modify other calendar events. Calendar data never leaves your device through BackDate.

### Notifications

BackDate schedules **local notifications** on your device — no notification server or push token is involved. Notification content (your step titles and dates) is processed entirely on-device. You can disable notifications at any time in iOS Settings → BackDate.

### Apple Watch

If you have a paired Apple Watch, BackDate uses Apple's WatchConnectivity framework to send goal data to the watch. This communication happens **directly between your iPhone and Apple Watch** — no server or internet connection is required.

### Home Screen Widget

The home screen widget displays your active goal's next step using data written to an on-device App Group container shared between the app and the widget. This data never leaves your device.

### .ics Export

When you export a goal as a calendar file (.ics), BackDate generates the file locally on your device and presents it through iOS's system share sheet. BackDate does not transmit this file anywhere.

---

## In-App Purchases

BackDate offers a one-time lifetime unlock purchase. Payments are processed entirely by **Apple's App Store** using the StoreKit framework. BackDate does not have access to your payment information, Apple ID, or billing details. Purchase records are managed by Apple and governed by [Apple's Privacy Policy](https://www.apple.com/legal/privacy/).

---

## Third-Party Services

BackDate does not integrate any third-party analytics, advertising, crash reporting, or tracking SDKs. No data is shared with or sold to third parties.

---

## Data Retention and Deletion

Your data exists on your device (and optionally in your iCloud account). You can delete all BackDate data by:

- Deleting individual goals within the app
- Deleting the BackDate app from your device (this removes all local data)
- Managing or deleting iCloud data in iOS Settings → Apple ID → iCloud → Manage Storage

---

## Children's Privacy

BackDate does not knowingly collect personal information from children under 13. The app contains no account creation, social features, or data collection mechanisms that would implicate children's privacy regulations.

---

## Changes to This Policy

If this privacy policy changes materially, we will update the "Last updated" date at the top of this page. Continued use of BackDate after changes constitutes acceptance of the updated policy.

---

## Contact

Questions about this privacy policy? Contact us at:

**moonbeamalphadev@gmail.com**
