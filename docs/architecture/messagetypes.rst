Common Message and Data Structure Definitions
=============================================

The following is a list of message and data schemas that are necessary for
dploy. These structures are generally used to define communication protocols
between various services. They should be language agnostic.


.. _build-request-msg-type:

BuildRequest
------------

Used to describe build jobs. These are sent to the DeployQueue.

Schema
~~~~~~

    .. describe:: broadcast_id
    
        A broadcast id of the format *[random-uuid]:[commit]*

    .. describe:: app
    
        The app name
    
    .. describe:: archive_uri
    
        URI to a tar.gz of the app
    
    .. describe:: commit
    
        The SHA1 commit of the app
    
    .. describe:: update_message
    
        A message about the update
    
    .. describe:: release_version
        
        The release version to use. 0 means the latest version


.. _broadcast-message-msg-type:

BroadcastMessage
----------------

Used for broadcasting messages to the client

Schema
~~~~~~

    .. describe:: type

        The message type

        Must be ``output`` or ``status``

    .. describe:: body
        
        The message body
        
        Must be data of type :ref:`broadcast-output-data-sub-data-type` or 
        :ref:`broadcast-status-data-sub-data-type`


.. _broadcast-output-data-sub-data-type:

BroadcastOutputData
^^^^^^^^^^^^^^^^^^^

    .. describe:: type
        
        Must be ``line`` or ``raw``

    .. describe:: data
        
        *(optional)* output string


.. _broadcast-status-data-sub-data-type:

BroadcastStatusData Schema
^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. describe:: type
        
        Must be ``info``, ``error``, or ``completed``

    .. describe:: data
        
        *(optional)* A status message


.. _app-build-request-msg-type:

AppBuildRequest
---------------

Used to describe app build jobs. These are sent to the BuildCenter.
They are created by processing DeployRequests.

Schema
~~~~~~

    .. describe:: app_release
        
        The current :ref:`app-release-data-type`

    .. describe:: archive_uri

        URI to a tar.gz file of the app's repository


.. _app-release-data-type:

AppRelease
----------

Used throughout different sections of the build process. It is also a major
component of the cargo file. These snapshots are also used to track versions of
a particular app.

Schema
~~~~~~

    .. describe:: version

        The release version number

    .. describe:: app

        The app name

    .. describe:: commit

        The SHA1 commit of the app

    .. describe:: env
        
        An :ref:`env-vars-data-type` type

    .. describe:: processes

        A dict of the available processes and their associated commands


.. _env-vars-data-type:

EnvVars
-------

Dictionary of services and their environment variables. This is meant to be
persisted in some kind of database. 


.. _zone-deploy-order-msg-type:

ZoneDeployOrder
---------------

Instructions for a dploy-zone to deploy an app given its cargo file.

Schema
~~~~~~

    .. describe:: app
        
        The app name

    .. describe:: cargo_uri

        URI to a downloadable cargo file


.. _zone-stop-deploy-msg-type:

ZoneStopDeploy
--------------

Stop a set of running apps

Schema
~~~~~~

    .. describe:: apps
        
        A list of apps to stop

