license for closed source
==========================

To request a commericial license for closed source projects and services

Definitions
------------

commercial license
"""""""""""""""""""
exclusion from the projects license, for a specific entity and time period

copyright holder
"""""""""""""""""

Someone who forks the project, simply by editting the legal notices, does
not suddenly become the copyright holder.

Under copyright law, a maintainer, having forked a project, cannot
request payment in the form of a license. Can only solicit for donations.

If required by the projects license, a commercial license
**must be** and **can only be** obtained from the copyright holder

How to contact
---------------

Encourage to send to multiple communication channels

- Mastodon

https://mastodon.social/@msftcangoblowme

- Email

`Dave Faulkmore <faulkmore@protonmail.com>`_

Why fund?
----------

Unfunded FOSS projects are instantly abandonware. Which should be a cause
for concern:

author attention is drawn away
"""""""""""""""""""""""""""""""

Often towards activities to make a living. Such as focusing on writing
unittests for web pages and smartphone apps.

Instead of producing jobs, companies self-interest is better served funding
talent to focus on maintaining the talent's piece of the FOSS
infrastructure.

author cannot attract maintainers
""""""""""""""""""""""""""""""""""

Common situation is the repository is in a preceived negative situation,
forcing others to fork the project and take on the enormous burden and
responsibility.

If the project is well funded, can garner maintainers time by compensating
them.

target for malware
"""""""""""""""""""

This is reoccurring real issue.

Maintainer(s) who step forward and have the talent, the author will depend on.

There being no non-subjective reprecussions for bad behavior or just to get
attention, at some point, in an innocent looking commit, malware gets introduced.

Obfusicated code is placed in either the build system or in unittest assets.

The swamp, drain-swamp is referring to, is the Makefile, untestable
shell scripts, and untestable Python scripts.

Minimizing the size of the swamp, reduces the attack surface; places
to hide dodgy code

xz is a project which had this issue. A now famous coder, thru what can
only be described as a miracle, tracked down the cause, and raised
awareness of the issue. The Linux communities quickly used an earlier
xz version or created a patch. The author did remove the malware,
which took some time. So **the xz author is a good actor**! And the
attack's impact on the world was minimized.

Procedure
----------

Communication
""""""""""""""

1. Contact the copyright holder

This is a negotiation. So can, make an offer.

2. discuss:

- terms and conditions

- pricing

3. The copyright holder should request and receive multiple contact
   means to keep in contact with requestor. Copyright holder must maintain
   this privacy data, in confidence, not share with any third party with
   the exception of maintainers and staff

Before any payments
""""""""""""""""""""

Verify the copyright holder **BEFORE** making any payments

Send some text message to have the copyright holder sign with PGP secret key.
The copyright holder will send back the signed message within a text file.

The message along with the PGP public key are used **to verify** the
copyright holder, signed it

Will receive
"""""""""""""

1. PGP public key file

   Which will be the same PGP public key used to sign commits.
   Instructions on how to confirm it's the same PGP public key.

2. PGP signed text file

   Contains the commercial license which is an exclusion, for a specific entity
   for a specific time period, from the projects license

Verify
"""""""

Will provide instructions on how to verify the PGP signed text file. Using
the PGP public key of the copyright holder

A text file not PGP signed or not signed by the copyright holder, is not an
authorized commercial license. Upon receipt, verify the PGP signature.
