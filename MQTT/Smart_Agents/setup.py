from setuptools import setup

setup(
    name='Flask-MQTT',
    version='0.0.1',
    url='https://github.com/etattershall/internet-of-thingies',
    license='MIT',
    author='Emma Tattershall, Callum Iddon',
    author_email='etat02@gmail.com',
    description='Collection of scripts & instructions for building IoT systems',
    packages=['piduino'],
    platforms='any',
    install_requires=[
        'Flask',
        'paho-mqtt'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python'
    ]
)
