try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from mediacore import __version__ as VERSION

install_requires = [
    'WebTest == 1.2',
    'Pylons == 0.10',
    'WebHelpers == 1.0',
    'SQLAlchemy >= 0.6.4',
    'sqlalchemy-migrate == 0.6',
    'Genshi == 0.6',
    'Babel == 0.9.5',
    'Routes == 1.12.3',
    'repoze.who == 1.0.18',
    'repoze.what-pylons == 1.0',
    'repoze.what-quickstart',
    'Paste == 1.7.4',
    'PasteDeploy == 1.3.3',
    'PasteScript == 1.7.3',
    'ToscaWidgets == 0.9.9',
    'tw.forms == 0.9.9',
    'BeautifulSoup == 3.0.8.1',
        # We monkeypatch this version of BeautifulSoup in mediacore.__init__
        # Patch pending: https://bugs.launchpad.net/beautifulsoup/+bug/397997
    'akismet == 0.2.0',
    'feedparser >= 4.1', # needed only for rss import script
    'cElementTree >= 1, < 2',
    'gdata > 2, < 2.1',
    'unidecode',
    'importlib',
    'decorator',
    'simplejson',
    'Babel',
    'Pillow',
    # kiberpipa
    'icalendar',
    'pytz',
    'supervisor',
    'fabric',
    'ielectric.fab',
    'gunicorn',
    'repoze.who.plugins.ldap',
    'psycopg2',
]

extra_arguments_for_setup = {}

# optional dependency on babel - if it is not installed, you can not extract
# new messages but MediaCore itself will still work...
try:
    import babel
except ImportError:
    pass
else:
    # extractors are declared separately so it is easier for 3rd party users
    # to use them for other packages as well...
    extractors = [
        ('lib/unidecode/**', 'ignore', None),
        ('tests/**', 'ignore', None),
        ('**.py', 'python', None),
        ('templates/**.html', 'genshi', {
                'template_class': 'genshi.template.markup:MarkupTemplate'
            }),
        ('public/**', 'ignore', None),
    ]
    extra_arguments_for_setup['message_extractors'] = {'mediacore': extractors}

setup(
    name='MediaCore',
    version=VERSION,
    description='A audio, video and podcast publication platform.',
    author='Simple Station Inc.',
    author_email='info@simplestation.com',
    url='http://getmediacore.com/',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Framework :: TurboGears :: Applications',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP :: Site Management'
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Multimedia :: Sound/Audio',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        ],

    install_requires=install_requires,
    paster_plugins=[
        'PasteScript',
        'Pylons',
    ],

    test_suite='nose.collector',
    tests_require=[
        'WebTest',
        ],

    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    package_data={'mediacore': ['i18n/*/LC_MESSAGES/*.mo']},
    zip_safe=False,

    entry_points="""
    [paste.app_factory]
    main = mediacore.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,

    **extra_arguments_for_setup
)
