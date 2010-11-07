Migration from old Cyberpipe arhive
===================================

Let's say your mediacore installation lies in ~/mediacore/

* connect to arhivar@dogbert.kiberpipa.org and run "python migration_to_mediacore.py"
* copy migration_to_mediacore.paypay.py to ~/mediacore/data.py
* python batch-scripts/import/old_kiberpipa_arhive_import.py develop.ini


CHANGELOG
=========

Initial release
---------------

- added THANKS page
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
