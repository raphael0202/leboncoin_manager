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

    import leboncoinManager

    #Read a gro file
    title, atoms, box = groio.parse_file("filin.gro")

    #Write a gro file
    with open("filout.gro", "w") as f:
        for line in groio.write_gro(title, output_atoms, box):
            print(line, end='', file=f)

    #Renumber the atoms to avoid number above 100 000
    atoms = groio.renumber(atoms)


The function ``parse_file`` returns :

- ``title``: the title of the system as written on line 1 of the file  as a string
- ``atoms``: a list of atom, each atom is stored as a dictionary
- ``box``: the box description as written on the last line as a string


Run tests
---------

Unit tests are available through `nosetests python module <https://nose.readthedocs.org>`_.
    nosetests tests/test_groio.py
