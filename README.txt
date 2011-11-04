
MicroBank is a sample application that uses the WingCash API. This sample
will grow as the WingCash API grows.

Getting Started
===============

MicroBank is based on Pyramid. There are various ways to run it, but the
easiest is probably to use Buildout[1]. Follow the instructions below to use
Buildout.

1. On your own computer, install Python and virtualenv. If you're using
   Ubuntu, you can simply install the ``python-virtualenv`` and ``python-dev``
   packages.

2. Check out MicroBank from github::

    git clone git://github.com/WingCash/MicroBank.git

3. Set up your virtualenv::

    cd MicroBank
    virtualenv --no-site-packages .

4. Bootstrap and run Buildout::

    bin/python bootstrap.py
    bin/buildout

5. Run MicroBank::

    ./run.sh

6. Visit MicroBank with your web browser to confirm it works:

    http://127.0.0.1:7100/

7. Add an application to your WingCash profile. Make a note of the client ID
   and client secret you receive.

    https://wingcash.com/developer/app/create

8. Configure your MicroBank app with the client ID and client secret you
   received.

    http://127.0.0.1:7100/configure

9. Log in to MicroBank using WingCash. Authorize your MicroBank instance to
   use your WingCash profile.

    http://127.0.0.1:7100/login

10. Your private MicroBank instance can now read the amount in your WingCash
    wallet. Congratulations! Browse the code[2], modify it, and have fun.

    
[1] http://buildout.org

[2] https://github.com/WingCash/MicroBank
