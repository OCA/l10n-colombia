[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/195/9.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-l10n-columbia-201)
[![Build Status](https://travis-ci.org/OCA/l10n-columbia.svg?branch=9.0)](https://travis-ci.org/OCA/l10n-columbia)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-columbia/badge.svg?branch=9.0&service=github)](https://coveralls.io/github/OCA/l10n-columbia?branch=9.0)
[![Code Climate](https://codeclimate.com/github/OCA/l10n-columbia/badges/gpa.svg)](https://codeclimate.com/github/OCA/l10n-columbia)

Localización Colombia: Terceros
======

![main_screenshot.png](http://www.plastinorte.com/images/main_screenshot.png)

Local Rules
-----------------
In Colombia there are some local rules that have to apply when creating a new contact. 
This module is designed from the legal requirements of the tax authority in Colombia.

- It is quite common that persons have up to 4 names. All of these are important to separate.
- The CIIU Code of a company shows the Industrial Classification of a company. This information will be important for tax calculation and statistics
- In Colombia there are many types of identification that have to be very clear in almost every transaction.
- NIT is the identification number for almost every company. The verification code will be calculated automatically.

What you get
-----------------
- Redesign of the contact form due to the above mentioned local rules that have to apply in Colombia:
- Additional fields: first name, second name, last name, second last name
- Additional fields: Type of Person, Document Type, Document Number, Tributate regime, CIIU Code
- Handling all kind of identification types that are relevant in Colombia
- Intelligent form: Fields will be checked for correctness and completeness
- Identification Number added into Tree View
- Identification Number added into KanBan View
- Visual Identifier for incomplete contacts in Kanban- and Tree view
- Auto-Complete of NIT: Type in the NIT and the Verification Digit will be calculated automatically
- Description of economic activities (CIIU Code), including the entire list to maintain it
- Maintain the CIIU list under this new menu point: Accounting/Configuration/Accounting/CIIU
- Contacts can be found by Identification Number (e.g. NIT)
- Added a complete list of all cities and departments in Colombia
- Country, Department and Municipality Dependency Logic in order to avoid confusion of locations with the same name
- Identification / Document-Type combination will be checked as it should be unique
- All changes available in english (choose language: en_GB)

How to install
-----------------
Setup a running environment of Odoo on your machine (local or remote). Here are two links on how to install odoo locally on Ubuntu and Mac: 
Ubuntu: https://goo.gl/mgEbUR
Mac: http://goo.gl/hXBqfG

Once you have a running installation, you can install this module on several ways: 

1. Go to your Addons folder of your Odoo Installation and type "git clone <repository-master>". 

2. You can download the ZIP file and extract all files. Have in mind that the folder you will add to your addons path is called "l10n_co_res_partner".

3. Install Docker on your computer and follow this instructions: https://goo.gl/5p8Q7Y


Restart your server and go the the applications tab. Change to developer mode and update the application list. Then you can search for the module like "colombia" or "Terceros". Install it. Have fun.

License
-----------------
Like many other modules for odoo, this project runs under the AGPL-3 license (http://www.gnu.org/licenses/agpl-3.0.html).
Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.


Feedback
-----------------
We want to improve constantly our software, therefore we love feedback. Feel free to comment at any time our code. 
If you think something is missing please don't hesitate to drop a message.


Contact
-----------------
This is how you can reach the contributors: 

Dominic Krimmer: dominic@plastinorte.com
Hector Ivan Valencia Muñoz: quipus.total@gmail.com
