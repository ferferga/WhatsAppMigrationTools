# WPWhatsAppToAndroid

This script will convert your existing Windows Phone's WhatsApp database to
the Android's schema.

## What do I need?

You need two databases: **messages.db** and **calls.db**, which you can get
using this [nice tutorial](https://web.archive.org/web/20201118142346/https://www.winwazzapmigrator.com/faq/windows-how-extract-messagesdb) from WinWazzapMigrator.

**calls.db** is not mentioned anywhere in the tutorial (as WinWazzapMigrator doesn't move them), however, it's located in **messages.db**'s directory, so you will spot it easily.

## Before starting

* **Windows users**: Download [here](https://github.com/ferferga/WhatsAppMigrationTools/releases) the latest available release.

* **Unix users**: Clone this repository and install the requirements as specified in the main 'README.md' file.

**ATTENTION!:** There are some part of the code designed to work only with Spain's phone numbers, so my contry code is used (+34). Go to lines **282**, **334** and **335** and change *34* with the phone code of your country. If you have contacts from other countries, you might need to do further changes to the code.

Also, take a look at lines **342** and **344**. There, (I'm not sure, as I never had my hand on a non-spanish database) I suspect that the ``s`` letter stands for 'Spain'. 

Open first your database with [SQLite Database Browser](https://sqlitebrowser.org/) and check the 'Jid' column in 'JidInfo' table to see how your contacts jids are stored.
Most of the records in that table should be something like +XXYYYYYYYYY@z.whatsapp.net (being **X** your country code, **Y** the phone number of your contact, and **z**). Ignore the rest, only pay attention to those that ends on ``@z.whatsapp.net``

Replace the ``s`` letter in the lines mentioned above if your **z** is different than ``s``.

Any PR to make this script easier to 'globalize' is appreciated!

(Of course, changing the lines in the code means that Windows users will need to run the script from its source, with Pyhton installed in their systems)

## Instructions

The process is really straightforward, everything is explained inside the script, so just follow the instructions.

After finishing, **don't remove any of the files**, you will need them later.

## Done! What's the next step?

Go over [here](https://github.com/ferferga/WhatsAppMigrationTools/blob/master/merger/README.md)!

## Issues

If facing any issues, publish the exception code received. For seeing it, just reproduce what you were doing again in a cmd or bash terminal, executing the script from there (instead of double clicking on it in the file browser), as the script might simply crash.

**IF YOU FACE AN ERROR, YOU ARE SUGGESTED TO NOT USE THE RESULTING *MSGSTORE.DB* DATABASE IN ANY OF THE FOLLOWING STEPS, AS YOU MIGHT END UP WITH AN INCOMPLETE OR INCOHERENT DATABASE**
