# WhatsApp Migration Tools

WhatsApp migration tools are my own set of utilities and documentation for moving WhatsApp databases from Windows Phone to Android, as well as a comprenhensive description of the 'forensics' involved in manipulating WhatsApp databases.

Previously known as [WAToAndroid](https://github.com/ferferga/WhatsAppMigrationTools/blob/1.0/README.md), I added one more tool and detailed instructions on how to successfully have a working setup after running my scripts (which I hope that will be really useful now, just after the dead of WhatsApp and WP)

My tools are different from others like [Whapa](https://github.com/B16f00t/whapa), as mine are designed to merge WP databases, which aren't covered in many other third-party tools.

### A bit of background

(Read the original description before reading this [here](https://github.com/ferferga/WhatsAppMigrationTools/blob/1.0/README.md), for even a better *background* =P)

Even though I said that this repository wouldn't receive any further updates, some other complications arose after publishing it. 

The original script was written between the middle and near the end of 2018, as I was already looking into switching back to Android after some years with my Lumia 640 XL, and also wanted to have another useful project in hands for learning. 
I tested restoring the resulting DB in an spare Android phone I got and it was a success back then.

However, I got a new phone just at the end of January 2019. I tried my own script without success, as WhatsApp already changed the way the restore process works,
not allowing local unencrypted backups to be restored. As I already had everything moved over to my new phone (confident that it would work), I was in a rush to get WhatsApp moved over as well. I discovered then ``WinWazzapMigrator``
an app made by *Nicola Beghin* (who seems that had the same problem I had and wanted to solve it) that served me perfectly. As my script proved to be useless, around that date, I decided to upload it here for people who might find it useful anyway (although it was already probably useless for everyone, not just me).

However, during this 2019 year, I discovered some issues with WinWazzapMigrator that really annoyed me:

* There was a starred message that crashed the app everytime I opened the 'Starred messages' section of the app.
* Messages quotes and mentions were completely away.
* All the call logs were missing
* I decided to not carry media over to the import, in order to save some space. However, even if I wouldn't be able to download them again (because WhatsApp couldn't locate them in the internal storage of my phone) I thought that WinWazzapMigrator would carry over the blurry thumbnails (example below) and placeholders for voice notes and all the media.

<p align="center">
  <img src="https://github.com/ferferga/WhatsAppMigrationTools/raw/master/images/blurred_media.jpg">
</p>

All these problems led me to many of my conversations lacking any sense. Also, I became aware afterwards that I could simply use a rooted Android system to access WhatsApp data. I started to investigate around this and I finally decided to write another tool to fix those quirks and merge both databases.

## Project structure

A brief description of the folders included in this repository:
* apk: This folder contains ``WhatsApp 2.18.248`` apk's, as they are known to be the last version where WhatsApp allowed the restore of local encrypted/unencrypted backups. This might be useful if you are moving from WP to Android directly without using WinWazzapMigrator.

* converter: This folder contains the old ``WindowsToAndroidWhatsApp`` (renamed to ``WPWhatsAppToAndroid`` + some tiny changes from last commit for simplifying the job to the ``merger.py`` script). This script will convert your Windows Phone databases to the old schema used in Android databases.

* images: Just images for the documentation

* merger: This folder contains the script that will merge your old WP database with an existing Android database (created by the WhatsApp app in Android).

* samples: This folder contains sample databases of each type for those aiming to upgrade my script if they stop working (if that's the case, please, make a PR!) or for other research purposes.

* LICENSE: Licensing information of this repository. This project is licensed under GPL3.

* requirements.txt: Being Python scripts, my script requires one module that you need to install before. If you're not under Windows, run ``pip install -r requirements.txt`` in your system to install the required module.

If you're a Windows user (or another OS user that needs bytecode Python for some reason), under the [Releases tab](https://github.com/ferferga/WhatsAppMigrationTools/releases) you will find pre-compiled Windows executables. Just extract them and run. No hassle.

## What do I need?

A clone of this repository made with ``git clone https://github.com/ferferga/WhatsAppMigrationTools`` and basic-intermediate computer knowledge (Please, if you think you get stuck during the process due to your knowledge, google a bit first, as the answer to your question might be out there already! That way, I would be able to help better and faster when needed)

## Where do I start?

Start first using the converter script called 'WPWhatsAppToAndroid', check over [here](https://github.com/ferferga/WhatsAppMigrationTools/blob/master/converter/README.md)!

## Is this for me?

This might be what you are looking for if:

* **You did use WinWazzapMigrator to move from WP to Android**: This is what I did, and what was tested

* **You moved to Android starting from scratch there a while ago, and now you want to bring back all your old WP messages to your current WhatsApp installation.**: This will likely be successful, although it wasn't tested by me (although [reports claim it works perfectly](https://github.com/ferferga/WhatsAppMigrationTools/issues/1#issuecomment-581165616))

* **You still didn't move from WP and don't want to buy WinWazzapMigrator**: My process is much more difficult and less user-friendly than theirs, but it will likely succeed as well, although it isn't tested. I would say however that this has less chances of being successful than the 2nd case. But worth trying I suppose, you will learn a lot along the way :).

If you see that any of the examples fits you, take a look anyway, as there are some things (like the *sorting database* part of the merger script) that can be helpful.

# DISCLAIMER

All of these tools and information provided here are intended for educational purposes and only in good faith. I don't encourage anyone, in any way, to try these methods to modify or extract databases of other people. Also, I **don't take any responsibility of what could happen when you use this information or tools I provide**

Although I will try and do my best to help you in case something goes wrong, WhatsApp changes databases very quickly (even if they don't end up implementing many of the features they start to code) and I might not be able to tell you how to solve an specific problem (specially because it might be caused by WinWazzapMigrator, if you used it before, instead of my scripts). So, **ALWAYS KEEP BACKUPS OF ABSOLUTELY EVERYTHING!**

# Credits

You are free to use this script and modify it as you want, but please, give credits if it you use any part of this work in yours. Also, if you improved something, don't hesitate to make a Pull Request!. 
If you're coming for a press, it's always great to get people from other sources coming to the repository and give their feedback on your original work, so please link to this as well if you make an article of this.

Everything that you have here is a product of countless hours (across many months)for researching, testing and writing the documentation, so I appreciate all of this.

Thank you very much!