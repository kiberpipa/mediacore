Migration from old Cyberpipe arhive
===================================

Let's say your mediacore installation lies in ~/mediacore/

* connect to arhivar@dogbert.kiberpipa.org and run "python migration_to_mediacore.py"
* copy migration_to_mediacore.paypay.py to ~/mediacore/data.py
* python batch-scripts/import/old_kiberpipa_arhive_import.py develop.ini


Development
===========

    $ virtualenv --no-site-packages -p python2.6 mediacore
    $ cd mediacore
    $ source bin/activate
    $ python setup.py develop
    $ vim development.ini
    $ paster setup-app
    $ paster serve


Deployment
==========

    $ fab deploy_pylons


CHANGELOG
=========

Initial release
---------------

- added THANKS page
- implemented LDAP support with user object
- about text
    * templates/media/explore.html
- bigger SLUG column size (100)
- live.html page
- python import script for conversion from old arhive
    * batch-scripts/import/old_kiberpipa_arhive_import.py
- implement Cyberpipe storage to support our folder structure
    * lib/storage/cyberpipe.py
- rewrite legacy urls to new ones
    * config/routing.py
