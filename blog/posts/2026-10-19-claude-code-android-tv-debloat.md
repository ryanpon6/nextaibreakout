---
title: "AI didn't invent Android TV debloating, but one repo says it's now a 15-minute job"
description: "People are using Claude Code to disable bloat and home-screen ad rows on Android and Google TVs over ADB. What it does, what it doesn't, and how to do it safely."
date: 2026-10-19
status: published
slug: claude-code-android-tv-debloat
seo_title: "Claude Code Android TV Debloat: cleanyourtv Explained"
seo_description: "How people use Claude Code and the cleanyourtv repo to debloat Android and Google smart TVs over ADB: what it does, what it doesn't, and how to do it safely."
keywords: "Claude Code, Android TV, Google TV, debloat, smart TV, ADB, cleanyourtv"
---

Posts saying Claude Code fixed people's smart TVs spread fast this weekend. Some is real, some is stretched. Here's what the original posts and the repo actually show.

## What happened

It started with Ryan Doyle (@doooyle) on Oct 16 at 2:44 PM MT. He posted that he "hacked" his TCL TV with Claude Code, and in a follow-up video at 6:07 PM MT he showed how fast it moves now. In his replies he said it's an Android TV and it was all done over Wi-Fi.

The post that really spread came from Gathin (@gathint) on Oct 17 at 2:51 AM MT. He gave Claude Code the model number of a Xiaomi Redmi 4A TV, and it "found the TV on wifi, removed 25 Xiaomi packages and wrote a new launcher." That post passed 4.7M impressions. He later clarified that nothing was deleted: the packages were disabled for the user profile, and the firmware was untouched.

Gathin put the prompt, the launcher and backup and restore tools in a public GitHub repo, now called cleanyourtv. It was created on Oct 17 and passed 3,400 stars by Oct 19 morning. It has 30 TV lists, from TCL and Sony to Nvidia Shield.

Ansub (@justansub) posted his own run on Oct 17 at 11:08 AM MT, on "my parents' old Android TV". He says free RAM went up about 90%. That's his own report. The speed claims in general come from the people who did it, not from independent tests.

It's FOSS covered the trend on Oct 19.

## What it actually does

It's standard Android tooling. You turn on developer options and USB or network debugging on the TV. A computer on the same Wi-Fi connects with `adb connect`, and you accept the prompt on the TV.

From there, Claude Code lists the installed packages and disables the bloat, telemetry and home-screen ad or recommendation services with `pm disable-user --user 0`. That's reversible with `pm enable`. Then it installs a lightweight launcher and sets it as Home. No root, no flashing.

The README's claim is where the "15 minutes" comes from: "With this repo as context it takes about fifteen minutes." That's the repo's own number, not an independent test.

## What it doesn't do

- **It's for Android-based TVs only.** It doesn't work on Samsung Tizen, LG webOS or Roku, per It's FOSS. Fire TV gets the debloat half only, because, per the README, "Fire OS will not hand Home to a third-party launcher."
- **LG claims are thin.** One LG owner had Claude press through the normal app menu, deleting apps users can already remove. A real webOS debloat needs root.
- **It doesn't remove ads inside streaming apps.** It only strips home-screen ads and rows. Doyle said he only cleared the ads from his home screen, not YouTube's.
- **The Stripe dashboard isn't a TV feature.** The revenue and Stripe payment screen in Doyle's post was his own custom screensaver, served from his Mac mini.

## Is it new?

Not really. ADB debloating and launcher swaps are a long-running hobbyist trick. An r/AndroidTV guide for the Onn 4K box uses the same `pm disable-user` launcher commands (its exact post date is unverified).

What's new is who can do it. The agent sorts the packages, finds the brand-specific bloat and writes the launcher, so people who'd never type an ADB command can do it in an afternoon. That's the interesting part.

## The risks

- **Open ADB is a door into your TV.** An open ADB port gives shell access to the device. In 2018 the ADB.Miner worm infected thousands of Android TVs and boxes that had port 5555 open.
- **You're giving an agent shell access.** The agent gets a shell on a device on your home network, running scripts from a days-old repo. Read them first.
- **You can break things.** Disabling the wrong package can kill HDMI input switching, the remote, the keyboard, updates or Home. One prompt warns that disabling the stock launcher before the new one is installed leaves a black screen.
- **You may lose updates.** Many debloat lists disable the maker's updater, which stops security fixes.
- **Rooting is a different level of risk.** RootMyTV warns that writing system partitions or using `chattr` can brick a TV. Rooting may also affect your warranty. We haven't checked the warranty terms of TCL, Xiaomi, LG or Google.

## Short safety checklist

1. Back up the package list before anything is changed.
2. Disable apps, don't uninstall them.
3. Never disable the launcher, input, remote or keyboard services.
4. Install the new launcher before touching the stock one.
5. Decide on purpose whether to keep the updater.
6. Turn ADB debugging off when you're done, and never expose the TV to the internet.

Got a slow, ad-heavy Android TV? It's worth an afternoon. Just know it's a home-screen cleanup, not an ad blocker.

## Sources

- [Ryan Doyle, origin post (Oct 16)](https://x.com/doooyle/status/2111196679680540724)
- [Doyle, speed follow-up](https://x.com/doooyle/status/2111247627748565091)
- [Doyle, screensaver dashboard reply](https://x.com/doooyle/status/2111222123419042218)
- [Doyle, in-app ads reply](https://x.com/doooyle/status/2111235718685057517)
- [Gathin, original post (Oct 17)](https://x.com/gathint/status/2111379569030939102)
- [Gathin, clarification](https://x.com/gathint/status/2111812538153496819)
- [cleanyourtv repo and README](https://github.com/Gathin23/cleanyourtv)
- [Ansub's post (Oct 17)](https://x.com/justansub/status/2111504666861379644)
- [toki, LG webOS run (Oct 18)](https://x.com/tokifyi/status/2111721895016219091)
- [It's FOSS coverage (Oct 19)](https://itsfoss.com/news/debloat-smart-tv/)
- [r/AndroidTV guide (date unverified)](https://www.reddit.com/r/AndroidTV/comments/12rya0t/change_launcher_debloat_the_new_onn_4k_streaming/)
- [Netlab 360 on ADB.Miner (2018)](https://blog.netlab.360.com/early-warning-adb-miner-a-mining-botnet-utilizing-android-adb-is-now-rapidly-spreading-en/)
- [BleepingComputer on ADB.Miner (2018)](https://www.bleepingcomputer.com/news/security/android-devices-targeted-by-new-monero-mining-botnet/)
- [cobanov TV prompt](https://tv.cobanov.dev/)
- [RootMyTV warning](https://rootmy.tv/warning)
