.. _install_apache-wsgi:

============================
Apache & mod_wsgi Deployment
============================

**NOTE 1:** This tutorial assumes that you already have Apache and mod_wsgi installed.
If you're on a shared hosting platform, and don't have the ability to install
mod_wsgi, have no fear. Your hosting provider probably already supports
mod_fastcgi so check out the :ref:`install_apache-fastcgi` tutorial.

**NOTE 2:** If you're administrating your own system and looking for pointers on how
to get mod_wsgi installed, check out the developer's site; the documentation is
verbose, but very complete: `mod_wsgi main site
<http://code.google.com/p/modwsgi/wiki/InstallationInstructions>`_.

Components
----------
The following five components are involved in getting web requests through to
mediacore with this setup. Don't worry if this sounds like a lot! By this
stage you already have three, and the remaining ones are very easy to set up.

``Apache``
   the web server

``mod_wsgi``
   Apache module that lets Apache host WSGI enabled Python applications

``httpd.conf``
   Your apache configuration; tells mod_wsgi how to run your app

``mediacore.wsgi``
   The script that runs mediacore as a WSGI application

``mediacore``
   the reason we're here!

Instructions
------------
**NOTE 1:** The following instructions assume that you're deploying MediaCore
to ``http://yourdomain.com/my_media/``. To deploy mediacore to any other path,
simply replace all references to ``/my_media`` below with your desired path.

**NOTE 2:** We will not actually be creating a ``my_media`` directory, but we
will use aliases in the Apache config to make sure that requests to
``http://yourdomain.com/my_media/`` are passed to MediaCore.

First, create a temporary directory and a python cache directory for your
deployment to use.

.. sourcecode:: bash

   cd /path/to/mediacore_install/data
   mkdir tmp
   mkdir python-egg-cache

**Permissions:**
Now is a good time to make sure that all of the apropriate files have the
correct permissions. The following files/directories should be writeable by
your apache user.
(Depending on how your server is set up, the user name may be different).

1. ``/path/to/mediacore_install/deployment-scripts/mod_wsgi/wsgi.pid``
#. ``/path/to/mediacore_install/mediacore/public/images/podcasts/``
#. ``/path/to/mediacore_install/mediacore/public/images/media/``
#. all of the folders inside the ``/path/to/mediacore_install/data/``

Second, you'll need to edit the paths in ``/path/to/mediacore_install/deployment-scripts/mod_wsgi/mediacore.wsgi``
to point to your own mediacore installation and virtual environment. The
**two (2)** lines you need to edit are at the top of the file, and look like
this:

.. sourcecode:: python

   deployment_config = '/path/to/mediacore_install/deployment.ini'
   temp_dir = '/path/to/mediacore_install/data/tmp'

Third, edit one line in ``/path/to/mediacore_install/deployment.ini``. Find
the proxy_prefix line, uncomment it, and set the prefix to ``/my_media``. This
will ensure that the URLs generated within the application point to the right
place:

.. sourcecode:: ini

   proxy_prefix = /my_media

Finally, you will need to add the following lines to your Apache configuration.
Depending on your setup, you may want to add it to the main ``httpd.conf`` file,
or inside a VirtualHost include.

Make sure that you replace all references to ``/path/to/mediacore_install/``
and ``/path/to/mediacore_env`` with the correct paths for your own MediaCore
installation and virtual environment.

.. sourcecode:: apacheconf

    # You can tweak the WSGIDaemonProcess directive for performance, but this
    # will work for now.
    # Relevant doc pages:
    #     http://code.google.com/p/modwsgi/wiki/ProcessesAndThreading
    #     http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess
    # Hint: pay attention to issues surrounding worker-mpm and prefork-mpm.

    WSGIDaemonProcess mcore \
        threads=10 \
        display-name=%{GROUP} \
        python-path=/path/to/mediacore_env/lib/python2.5/site-packages \
        python-eggs=/path/to/mediacore_install/data/python-egg-cache

    WSGIProcessGroup mcore

    # Intercept all requests to /my_media/* and pass them to mediacore.wsgi
    WSGIScriptAlias /my_media /path/to/mediacore_install/deployment-scripts/mod_wsgi/mediacore.wsgi

    # Make the url accessible (just in case it's not already)
    <Location "/my_media">
        Allow from all
    </Location>

    # Make the wsgi script accessible
    <Directory /path/to/mediacore_install/deployment-scripts/mod_wsgi>
        Order allow,deny
        Allow from all
    </Directory>

    # Create an exception for media and podcast image from your data directory
    AliasMatch /my_media/images/(media|podcasts)(.*) /path/to/mediacore_install/data/images/$1$2

    # Create an exception for all static mediacore content
    AliasMatch /my_media/(admin/)?(images|scripts|styles)(.*) /path/to/mediacore_install/mediacore/public/$1$2$3

    # Make all the static content accessible
    <Directory /path/to/mediacore_install/mediacore/public/*>
        Order allow,deny
        Allow from all
        Options -Indexes
    </Directory>

Performance Enhancements
------------------------
By default, all files are served through MediaCore. The configuration above
ensures that Apache will serve all static files (.css, .js, and images)
directly, but MediaCore will still check for static files before serving any
page. There are two speedups we can enable here.

First, edit one line in ``/path/to/mediacore_install/deployment.ini``. Find
the static_files line, and set it to false.

.. sourcecode:: ini

   static_files = false

The second speedup is only available if you have mod_xsendfile installed and
enabled in Apache. MediaCore can take advantage of mod_xsendfile and have
Apache serve all media files (.mp3, .mp4, etc.) directly. To enable this, edit
another line in ``/path/to/mediacore_install/deployment.ini``. Find the
files_serve_method line, and set it to apache_xsendfile.

.. sourcecode:: ini

   files_serve_method = apache_xsendfile

Editing MediaCore
-----------------
If you make any changes to your MediaCore installation while Apache is running
(eg. if you upgrade MediaCore or make any customizations), you'll need to make
sure that mod_wsgi recognizes those changes.

The easiest way to do this is to 'touch' the .wsgi script. This will modify the
'last modified on' timestamp of the file, so that mod_wsgi thinks it has been
updated and will read and re-load it.

.. sourcecode:: bash

   # Navigate to the mod_wsgi directory
   cd /path/to/mediacore_install
   cd deployment-scripts/mod_wsgi

   # Force a refresh of the mediacore code
   touch mediacore.wsgi
