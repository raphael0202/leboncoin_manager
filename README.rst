LeboncoinManager
=======================

A module to easily manage your ads on leboncoin.fr. Owing an account
on leboncoin.fr is mandatory.
Available actions:
- publish a new ad
- push an existing ad on the top of the ad list
- delete an ad

Installation
------------

    pip install leboncoin_manager

Usage
-----

.. code:: python

    from leboncoinManager import leboncoinManager

    #Connect to your account
    manager = leboncoinManager("username", "password")

    #push an existing ad on the top of the list
    manager.update("ad title") # "ad title" is the title visible on leboncoin.fr

You can use the provided CLI ``leboncoin_manager`` to manage your ads:
    leboncoin_manager -c ads.conf

A configuration file example is provided ('update.conf').
