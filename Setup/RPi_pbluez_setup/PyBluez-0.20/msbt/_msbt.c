#include <winsock2.h>
#include <ws2bth.h>
#include <BluetoothAPIs.h>

#include <Python.h>

#include <initguid.h>
#include <port3.h>


#if 1
static void dbg(const char *fmt, ...)
{
}
#else
static void dbg(const char *fmt, ...)
{
    va_list ap;
    va_start (ap, fmt);
    vprintf (fmt, ap);
    va_end (ap);
}
#endif

static void Err_SetFromWSALastError(PyObject *exc)
{
	LPVOID lpMsgBuf;
	FormatMessage( FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL, WSAGetLastError(), 0, (LPTSTR) &lpMsgBuf, 0, NULL );
    PyErr_SetString( exc, lpMsgBuf );
	LocalFree(lpMsgBuf);
}


#define _CHECK_OR_RAISE_WSA(cond) \
        if( !(cond) ) { Err_SetFromWSALastError( PyExc_IOError ); return 0; }

static void
ba2str( BTH_ADDR ba, char *addr )
{
    int i;
    unsigned char bytes[6];
    for( i=0; i<6; i++ ) {
        bytes[5-i] = (unsigned char) ((ba >> (i*8)) & 0xff);
    }
    sprintf(addr, "%02X:%02X:%02X:%02X:%02X:%02X", 
            bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5] );
}

static PyObject *
msbt_initwinsock(PyObject *self)
{
    WORD wVersionRequested;
    WSADATA wsaData;
    int status;
    wVersionRequested = MAKEWORD( 2, 0 );
    status = WSAStartup( wVersionRequested, &wsaData );
    if( 0 != status ) {
        Err_SetFromWSALastError( PyExc_RuntimeError );
        return 0;
    }

    Py_INCREF( Py_None );
    return Py_None;
}
PyDoc_STRVAR(msbt_initwinsock_doc, "TODO");

static void 
dict_set_str_pyobj(PyObject *dict, const char *key, PyObject *valobj)
{
    PyObject *keyobj;
    keyobj = PyString_FromString( key );
    PyDict_SetItem( dict, keyobj, valobj );
    Py_DECREF( keyobj );
}

static void 
dict_set_strings(PyObject *dict, const char *key, const char *val)
{
    PyObject *keyobj, *valobj;
    keyobj = PyString_FromString( key );
    valobj = PyString_FromString( val );
    PyDict_SetItem( dict, keyobj, valobj );
    Py_DECREF( keyobj );
    Py_DECREF( valobj );
}

static void 
dict_set_str_long(PyObject *dict, const char *key, long val)
{
    PyObject *keyobj, *valobj;
    keyobj = PyString_FromString( key );
    valobj = PyInt_FromLong(val);
    PyDict_SetItem( dict, keyobj, valobj );
    Py_DECREF( keyobj );
    Py_DECREF( valobj );
}

static int 
str2uuid( const char *uuid_str, GUID *uuid) 
{
    // Parse uuid128 standard format: 12345678-9012-3456-7890-123456789012
    int i;
    char buf[20] = { 0 };

    strncpy(buf, uuid_str, 8);
    uuid->Data1 = strtoul( buf, NULL, 16 );
    memset(buf, 0, sizeof(buf));

    strncpy(buf, uuid_str+9, 4);
    uuid->Data2 = (unsigned short) strtoul( buf, NULL, 16 );
    memset(buf, 0, sizeof(buf));
    
    strncpy(buf, uuid_str+14, 4);
    uuid->Data3 = (unsigned short) strtoul( buf, NULL, 16 );
    memset(buf, 0, sizeof(buf));

    strncpy(buf, uuid_str+19, 4);
    strncpy(buf+4, uuid_str+24, 12);
    for( i=0; i<8; i++ ) {
        char buf2[3] = { buf[2*i], buf[2*i+1], 0 };
        uuid->Data4[i] = (unsigned char)strtoul( buf2, NULL, 16 );
    }

    return 0;
}

// ====================== SOCKET FUNCTIONS ========================

static PyObject *
msbt_socket(PyObject *self, PyObject *args)
{
    int family = AF_BTH;
    int type;
    int proto;
    int sockfd = -1;

    if(!PyArg_ParseTuple(args, "ii", &type, &proto)) return 0;

    Py_BEGIN_ALLOW_THREADS;
    sockfd = socket( AF_BTH, type, proto );
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( SOCKET_ERROR != sockfd );

    return PyInt_FromLong( sockfd );
};
PyDoc_STRVAR(msbt_socket_doc, "TODO");

static PyObject *
msbt_bind(PyObject *self, PyObject *args)
{
    char *addrstr = NULL;
    int addrstrlen = -1;
    int sockfd = -1;
    int port = -1;
    char buf[100] = { 0 };
    int buf_len = sizeof( buf );
    int status;

    SOCKADDR_BTH sa = { 0 };
    int sa_len = sizeof(sa);

    if(!PyArg_ParseTuple(args, "is#i", &sockfd, &addrstr, &addrstrlen, &port))
        return 0;

    if( addrstrlen == 0 ) {
        sa.btAddr = 0;
    } else {
        _CHECK_OR_RAISE_WSA( NO_ERROR == WSAStringToAddress( addrstr, \
                    AF_BTH, NULL, (LPSOCKADDR)&sa, &sa_len ) );
    }
    sa.addressFamily = AF_BTH;
    sa.port = port;

    Py_BEGIN_ALLOW_THREADS;
    status = bind( sockfd, (LPSOCKADDR)&sa, sa_len );
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( NO_ERROR == status );

    Py_INCREF(Py_None);
    return Py_None;
};
PyDoc_STRVAR(msbt_bind_doc, "TODO");

static PyObject *
msbt_listen(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    int backlog = -1;
    DWORD status;
    if(!PyArg_ParseTuple(args, "ii", &sockfd, &backlog)) return 0;

    Py_BEGIN_ALLOW_THREADS;
    status = listen(sockfd, backlog);
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( NO_ERROR == status );
    
    Py_INCREF(Py_None);
    return Py_None;
};
PyDoc_STRVAR(msbt_listen_doc, "TODO");

static PyObject *
msbt_accept(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    int clientfd = -1;
    SOCKADDR_BTH ca = { 0 };
    int ca_len = sizeof(ca);
    PyObject *result = NULL;
    char buf[100] = { 0 };
    int buf_len = sizeof(buf);

    if(!PyArg_ParseTuple(args, "i", &sockfd)) return 0;
    
    Py_BEGIN_ALLOW_THREADS;
    clientfd = accept(sockfd, (LPSOCKADDR)&ca, &ca_len);
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( SOCKET_ERROR != clientfd );

    ba2str(ca.btAddr, buf);
    result = Py_BuildValue( "isi", clientfd, buf, ca.port );
    return result;
};
PyDoc_STRVAR(msbt_accept_doc, "TODO");

static PyObject *
msbt_connect(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    char *addrstr = NULL;
    int port = -1;
    SOCKADDR_BTH sa = { 0 };
    int sa_len = sizeof(sa);
    DWORD status;

    if(!PyArg_ParseTuple(args, "isi", &sockfd, &addrstr, &port)) return 0;

    if( SOCKET_ERROR == WSAStringToAddress( addrstr, AF_BTH, NULL, 
                (LPSOCKADDR)&sa, &sa_len ) ) {
        Err_SetFromWSALastError(PyExc_IOError);
        return 0;
    }
    sa.addressFamily = AF_BTH;
    sa.port = port;
    
    Py_BEGIN_ALLOW_THREADS;
    status = connect(sockfd, (LPSOCKADDR)&sa, sizeof(sa));
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( NO_ERROR == status );

    Py_INCREF(Py_None);
    return Py_None;
};
PyDoc_STRVAR(msbt_connect_doc, "TODO");

static PyObject *
msbt_send(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    char *data = NULL;
    int datalen = -1;
    int flags = 0;
    int sent = 0;

    if(!PyArg_ParseTuple(args, "is#|i", &sockfd, &data, &datalen, &flags)) 
        return 0;

    Py_BEGIN_ALLOW_THREADS;
    sent = send(sockfd, data, datalen, flags);
    Py_END_ALLOW_THREADS;

    if (WSAGetLastError() == WSAEWOULDBLOCK ||
        WSAGetLastError() == WSAETIMEDOUT ) {
		return PyInt_FromLong ( 0 );
	}


    _CHECK_OR_RAISE_WSA( SOCKET_ERROR != sent );
    
    return PyInt_FromLong( sent );
};
PyDoc_STRVAR(msbt_send_doc, "TODO");

static PyObject *
msbt_recv(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    PyObject *buf = NULL;
    int datalen = -1;
    int flags = 0;
    int received = 0;

    if(!PyArg_ParseTuple(args, "ii|i", &sockfd, &datalen, &flags))
        return 0;

    buf = PyString_FromStringAndSize((char*)0, datalen);
    Py_BEGIN_ALLOW_THREADS;
    received = recv(sockfd, PyString_AS_STRING(buf), datalen, flags);
    Py_END_ALLOW_THREADS;

    if (WSAGetLastError() == WSAEWOULDBLOCK ||
        WSAGetLastError() == WSAETIMEDOUT ) {
        _PyString_Resize(&buf, 0); // XXX is this necessary? -albert

        return buf;
    }

    if( SOCKET_ERROR == received ){
        Py_DECREF(buf);
        return 0;   
    }
    if( received != datalen ) _PyString_Resize(&buf, received);

    return buf;
};
PyDoc_STRVAR(msbt_recv_doc, "TODO");

static PyObject *
msbt_close(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    int status;
    if(!PyArg_ParseTuple( args, "i", &sockfd )) return 0;
    
    Py_BEGIN_ALLOW_THREADS;
    status = closesocket(sockfd);
    Py_END_ALLOW_THREADS;

    Py_INCREF(Py_None);
    return Py_None;
};
PyDoc_STRVAR(msbt_close_doc, "TODO");

static PyObject *
msbt_getsockname(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    SOCKADDR_BTH sa = { 0 };
    int sa_len = sizeof(sa);
    char buf[100] = { 0 };
    int buf_len = sizeof(buf);
    int status;
    if(!PyArg_ParseTuple( args, "i", &sockfd )) return 0;

    sa.addressFamily = AF_BTH;
    Py_BEGIN_ALLOW_THREADS;
    status = getsockname( sockfd, (LPSOCKADDR)&sa, &sa_len );
    Py_END_ALLOW_THREADS;

    _CHECK_OR_RAISE_WSA( NO_ERROR == status );

    ba2str( sa.btAddr, buf );
    return Py_BuildValue( "si", buf, sa.port );
};
PyDoc_STRVAR(msbt_getsockname_doc, "TODO");

static PyObject *
msbt_dup(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    int newsockfd = -1;
    int status;
    DWORD pid;
    WSAPROTOCOL_INFO pi = { 0 };

    if(!PyArg_ParseTuple( args, "i", &sockfd )) return 0;

    // prepare to duplicate
    pid = GetCurrentProcessId();
    status = WSADuplicateSocket( sockfd, pid, &pi );
    _CHECK_OR_RAISE_WSA( NO_ERROR == status );

    // duplicate!
    newsockfd = WSASocket( FROM_PROTOCOL_INFO, 
            FROM_PROTOCOL_INFO, 
            FROM_PROTOCOL_INFO,
            &pi, 0, 0 );
    _CHECK_OR_RAISE_WSA( INVALID_SOCKET != newsockfd );
    
    return PyInt_FromLong( newsockfd );
}
PyDoc_STRVAR(msbt_dup_doc, "TODO");

// ====================

static PyObject *
msbt_discover_devices(PyObject *self, PyObject *args)
{
    int flushcache = 0;
    int lookupnames = 0;
    int lookupclass = 0;

	// inquiry data structure
	DWORD qs_len = sizeof( WSAQUERYSET );
	WSAQUERYSET *qs = (WSAQUERYSET*) malloc( qs_len );

	DWORD flags = LUP_CONTAINERS;
	HANDLE h;
	int done = 0;
    PyObject *toreturn = NULL;
    int status = 0;

    dbg("msbt_discover_devices\n");

    if(!PyArg_ParseTuple(args, "iii", &flushcache, &lookupnames, &lookupclass)) {
        free( qs );
        return 0;
    }

    if (flushcache) flushcache = LUP_FLUSHCACHE;
    if (lookupnames) lookupnames = LUP_RETURN_NAME;
    if (lookupclass) lookupclass = LUP_RETURN_TYPE;

	ZeroMemory( qs, qs_len );
	qs->dwSize = sizeof(WSAQUERYSET);
	qs->dwNameSpace = NS_BTH;

	flags |= flushcache | lookupnames | lookupclass | LUP_RETURN_ADDR;

	Py_BEGIN_ALLOW_THREADS;
	// start the device inquiry
    status = WSALookupServiceBegin (qs, flags, &h);
    Py_END_ALLOW_THREADS;

	if (SOCKET_ERROR == status) {
        int error = WSAGetLastError();
        if( error == WSASERVICE_NOT_FOUND ) {
            dbg("No devices detected\n");

            // no devices detected.
            WSALookupServiceEnd( h );
            free( qs );
            PyErr_SetString (PyExc_IOError, "No Bluetooth adapter detected");
            return NULL;
        } else {
            Err_SetFromWSALastError( PyExc_IOError );
            free(qs);
            return 0;
        }
	}

    toreturn = PyList_New(0);

	// iterate through the inquiry results
	while(! done) {
        Py_BEGIN_ALLOW_THREADS;
        status = WSALookupServiceNext (h, flags, &qs_len, qs);
        Py_END_ALLOW_THREADS;

		if (NO_ERROR == status) {
			char buf[40] = {0};
            PyObject *tup = NULL;
			BTH_ADDR result = 
				((SOCKADDR_BTH*)qs->lpcsaBuffer->RemoteAddr.lpSockaddr)->btAddr;
            ba2str( result, buf );

			if( lookupnames && lookupclass ) {
                tup = Py_BuildValue( "ssl", buf, qs->lpszServiceInstanceName, qs->lpServiceClassId->Data1 );
			} else if( lookupnames ) {
                tup = Py_BuildValue( "ss", buf, qs->lpszServiceInstanceName );
			} else if (lookupclass) {
                tup = Py_BuildValue( "sl", buf, qs->lpServiceClassId->Data1 );
			} else {
                tup = PyString_FromString (buf);
            }
            PyList_Append( toreturn, tup );
            Py_DECREF( tup );
		} else {
			int error = WSAGetLastError();
			
			if( error == WSAEFAULT ) {
                // the qs data structure is too small.  allocate a bigger
                // buffer and try again.
				free( qs );
				qs = (WSAQUERYSET*) malloc( qs_len );
			} else if( error == WSA_E_NO_MORE ) {
                // no more results.
				done = 1;
			} else {
                // unexpected error.  raise an exception.
                Err_SetFromWSALastError( PyExc_IOError );
                Py_DECREF( toreturn );
                return 0;
			}
		}
	}
    Py_BEGIN_ALLOW_THREADS;
    WSALookupServiceEnd( h );
    Py_END_ALLOW_THREADS;
	free( qs );

    return toreturn;
}
PyDoc_STRVAR(msbt_discover_devices_doc, "TODO");

static PyObject *
msbt_lookup_name(PyObject *self, PyObject *args)
{
    HANDLE rhandle = NULL;
    BLUETOOTH_FIND_RADIO_PARAMS p = { sizeof(p) };
    HBLUETOOTH_RADIO_FIND fhandle = NULL;
    BLUETOOTH_DEVICE_INFO dinfo = { 0 };
    char *addrstr = NULL;
    SOCKADDR_BTH sa = { 0 };
    int sa_len = sizeof(sa);
    DWORD status;

    if(!PyArg_ParseTuple(args,"s",&addrstr)) return 0;
    
    _CHECK_OR_RAISE_WSA( NO_ERROR == WSAStringToAddress( addrstr, \
                AF_BTH, NULL, (LPSOCKADDR)&sa, &sa_len ) );

//    printf("looking for first radio\n");
    fhandle = BluetoothFindFirstRadio(&p, &rhandle);
    _CHECK_OR_RAISE_WSA( NULL != fhandle );
//    printf("found radio 0x%p\n", rhandle );

    dinfo.dwSize = sizeof( dinfo );
    dinfo.Address.ullLong = sa.btAddr;
    status = BluetoothGetDeviceInfo( rhandle, &dinfo );

    _CHECK_OR_RAISE_WSA( status == ERROR_SUCCESS );
//    printf("name: %s\n", dinfo.szName );

    _CHECK_OR_RAISE_WSA( TRUE == BluetoothFindRadioClose( fhandle ) );

    return PyUnicode_FromWideChar( dinfo.szName, wcslen( dinfo.szName ) );
}
PyDoc_STRVAR(msbt_lookup_name_doc, "TODO");

// ======================= SDP FUNCTIONS ======================

static PyObject *
msbt_find_service(PyObject *self, PyObject *args)
{
    char *addrstr = NULL;
    char *uuidstr = NULL;

	// inquiry data structure
	DWORD qs_len = sizeof( WSAQUERYSET );
	WSAQUERYSET *qs = (WSAQUERYSET*) malloc( qs_len );

	DWORD flags = LUP_FLUSHCACHE | LUP_RETURN_ALL;
	HANDLE h;
	int done = 0;
    int status = 0;
    PyObject *record = NULL;
    PyObject *toreturn = NULL;
    GUID uuid = { 0 };
    char localAddressBuf[20] = { 0 };

    if(!PyArg_ParseTuple(args,"ss", &addrstr, &uuidstr))
        return 0;

	ZeroMemory( qs, qs_len );
	qs->dwSize = sizeof(WSAQUERYSET);
	qs->dwNameSpace = NS_BTH;
    qs->dwNumberOfCsAddrs = 0;
    qs->lpszContext = (LPSTR) localAddressBuf;

    if( 0 == strcmp( addrstr, "localhost" ) ) {
        // find the Bluetooth address of the first local adapter. 
#if 0
        HANDLE rhandle = NULL;
        BLUETOOTH_RADIO_INFO info;
        BLUETOOTH_FIND_RADIO_PARAMS p = { sizeof(p) };
        HBLUETOOTH_RADIO_FIND fhandle = NULL;

        printf("looking for first radio\n");
        fhandle = BluetoothFindFirstRadio(&p, &rhandle);
        _CHECK_OR_RAISE_WSA( NULL != fhandle );

        printf("first radio: 0x%p\n", rhandle);
        _CHECK_OR_RAISE_WSA( \
                TRUE == BluetoothFindRadioClose( fhandle ) );

        printf("retrieving radio info on handle 0x%p\n", rhandle);
        info.dwSize = sizeof(info);
        // XXX why doesn't this work???
        _CHECK_OR_RAISE_WSA( \
            ERROR_SUCCESS != BluetoothGetRadioInfo( rhandle, &info ) );

        ba2str( info.address.ullLong, localAddressBuf );
#else
        // bind a temporary socket and get its Bluetooth address
        SOCKADDR_BTH sa = { 0 };
        int sa_len = sizeof(sa);
        int tmpfd = socket(AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);

        _CHECK_OR_RAISE_WSA( tmpfd >= 0 );
        sa.addressFamily = AF_BTH;
        sa.port = BT_PORT_ANY;
        _CHECK_OR_RAISE_WSA(NO_ERROR == bind(tmpfd,(LPSOCKADDR)&sa,sa_len) );

        _CHECK_OR_RAISE_WSA(NO_ERROR == getsockname(tmpfd, (LPSOCKADDR)&sa,\
                    &sa_len ) );

        ba2str(sa.btAddr, localAddressBuf );
        close(tmpfd);
#endif

        flags |= LUP_RES_SERVICE;
    } else {
        strcpy( localAddressBuf, addrstr );
    }

    if( strlen(uuidstr) != 36 || uuidstr[8] != '-' || uuidstr[13] != '-' 
            || uuidstr[18] != '-' || uuidstr[23] != '-' ) {
        PyErr_SetString( PyExc_ValueError, "Invalid UUID!");
        return 0;
    }

    str2uuid( uuidstr, &uuid );
    qs->lpServiceClassId = &uuid;

    Py_BEGIN_ALLOW_THREADS;
    status = WSALookupServiceBegin( qs, flags, &h );
    Py_END_ALLOW_THREADS;
	if( SOCKET_ERROR == status) {
        int err_code = WSAGetLastError();
        if( WSASERVICE_NOT_FOUND == err_code ) {
            // this device does not advertise any services.  return an
            // empty list
            free( qs );
            return PyList_New(0);
        } else {
            // unexpected error.  raise an exception
            Err_SetFromWSALastError( PyExc_IOError );
            free(qs);
            return 0;
        }
	}

    toreturn = PyList_New(0);

	// iterate through the inquiry results
	while(! done) {
        Py_BEGIN_ALLOW_THREADS;
        status = WSALookupServiceNext( h, flags, &qs_len, qs );
        Py_END_ALLOW_THREADS;
		if (NO_ERROR == status) {
            int proto;
            int port;
            PyObject *rawrecord = NULL;
            CSADDR_INFO *csinfo = NULL;

            record = PyDict_New();
            // set host name
            dict_set_strings( record, "host", localAddressBuf );
            
            // set service name
            dict_set_strings( record, "name", qs->lpszServiceInstanceName );

            // set description
            dict_set_strings( record, "description", qs->lpszComment );

            // set protocol and port
            csinfo = qs->lpcsaBuffer;
            if( csinfo != NULL ) {
                proto = csinfo->iProtocol;
                port = ((SOCKADDR_BTH*)csinfo->RemoteAddr.lpSockaddr)->port;

                dict_set_str_long(record, "port", port);
                if( proto == BTHPROTO_RFCOMM ) {
                    dict_set_strings(record, "protocol", "RFCOMM");
                } else if( proto == BTHPROTO_L2CAP ) {
                    dict_set_strings(record, "protocol", "L2CAP");
                } else {
                    dict_set_strings(record, "protocol", "UNKNOWN");
                    dict_set_str_pyobj(record, "port", Py_None);
                }
            } else { 
                dict_set_str_pyobj(record, "port", Py_None);
                dict_set_strings(record, "protocol", "UNKNOWN");
            }

            // add the raw service record to be parsed in python
            rawrecord = PyString_FromStringAndSize( qs->lpBlob->pBlobData, 
                    qs->lpBlob->cbSize );
            dict_set_str_pyobj(record, "rawrecord", rawrecord);
            Py_DECREF(rawrecord);

            PyList_Append( toreturn, record );
            Py_DECREF( record );
		} else {
			int error = WSAGetLastError();
			
			if( error == WSAEFAULT ) {
                // the qs data structure is too small.  allocate a bigger
                // buffer and try again.
				free( qs );
				qs = (WSAQUERYSET*) malloc( qs_len );
			} else if( error == WSA_E_NO_MORE ) {
                // no more results.
				done = 1;
			} else {
                // unexpected error.  raise an exception.
                Err_SetFromWSALastError( PyExc_IOError );
                Py_DECREF( toreturn );
                return 0;
			}
		}
	}
    Py_BEGIN_ALLOW_THREADS;
	WSALookupServiceEnd( h );
    Py_END_ALLOW_THREADS;
	free( qs );

    return toreturn;
}
PyDoc_STRVAR(msbt_find_service_doc, "TODO");

static PyObject *
msbt_set_service_raw(PyObject *self, PyObject *args)
{
    int advertise = 0;
    WSAQUERYSET qs = { 0 };
    WSAESETSERVICEOP op;

    char *record = NULL;
    int reclen = -1;
    BTH_SET_SERVICE *si = NULL;
    int silen = -1;
    ULONG sdpVersion = BTH_SDP_VERSION;
    BLOB blob = { 0 };
    int status = -1;
    PyObject *result = NULL;
    HANDLE rh = 0;

    if(!PyArg_ParseTuple(args, "s#i|i", &record, &reclen, &advertise, &rh))
        return 0;

    silen = sizeof(BTH_SET_SERVICE) + reclen - 1;
    si = (BTH_SET_SERVICE*) malloc(silen);
    ZeroMemory( si, silen );

    si->pSdpVersion = &sdpVersion;
    si->pRecordHandle = &rh;
    si->fCodService = 0;
    si->Reserved;
    si->ulRecordLength = reclen;
    memcpy( si->pRecord, record, reclen );
    op = advertise ? RNRSERVICE_REGISTER : RNRSERVICE_DELETE;

    qs.dwSize = sizeof(qs);
    qs.lpBlob = &blob;
    qs.dwNameSpace = NS_BTH;

    blob.cbSize = silen;
    blob.pBlobData = (BYTE*)si;

    status = WSASetService( &qs, op, 0 );
    free( si );

    if( SOCKET_ERROR == status ) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

    return PyInt_FromLong( (unsigned long) rh );
}
PyDoc_STRVAR(msbt_set_service_raw_doc, "");

static PyObject *
msbt_set_service(PyObject *self, PyObject *args)
{
    int advertise = 0;
    WSAQUERYSET qs = { 0 };
    WSAESETSERVICEOP op;

	SOCKADDR_BTH sa = { 0 };
	int sa_len = sizeof(sa);
    char *service_name = NULL;
    char *service_desc = NULL;
    char *service_class_id_str = NULL;
	CSADDR_INFO sockInfo = { 0 };
    GUID uuid = { 0 };
    int sockfd;

    if(!PyArg_ParseTuple(args, "iisss", &sockfd, &advertise, &service_name, 
                &service_desc, &service_class_id_str))
        return 0;

    op = advertise ? RNRSERVICE_REGISTER : RNRSERVICE_DELETE;

    if( SOCKET_ERROR == getsockname( sockfd, (SOCKADDR*) &sa, &sa_len ) ) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

	sockInfo.iProtocol = BTHPROTO_RFCOMM;
	sockInfo.iSocketType = SOCK_STREAM;
	sockInfo.LocalAddr.lpSockaddr = (LPSOCKADDR) &sa;
	sockInfo.LocalAddr.iSockaddrLength = sizeof(sa);
	sockInfo.RemoteAddr.lpSockaddr = (LPSOCKADDR) &sa;
	sockInfo.RemoteAddr.iSockaddrLength = sizeof(sa);

    qs.dwSize = sizeof(qs);
    qs.dwNameSpace = NS_BTH;
    qs.lpcsaBuffer = &sockInfo;
    qs.lpszServiceInstanceName = service_name;
    qs.lpszComment = service_desc;
    str2uuid( service_class_id_str, &uuid );
    qs.lpServiceClassId = (LPGUID) &uuid;
    qs.dwNumberOfCsAddrs = 1;

    if( SOCKET_ERROR == WSASetService( &qs, op, 0 ) ) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

    Py_INCREF( Py_None );
    return Py_None;
}
PyDoc_STRVAR(msbt_set_service_doc, "");

static PyObject *
msbt_setblocking(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    int block = -1;
    PyObject* blockingArg;

    if(!PyArg_ParseTuple(args, "iO", &sockfd, &blockingArg)) return 0;

    block = PyInt_AsLong(blockingArg);

    if (block == -1 && PyErr_Occurred())
        return NULL;

    if (block) {
        block = 0;
        ioctlsocket( sockfd, FIONBIO, &block);
    } else {
        block = 1;
        ioctlsocket( sockfd, FIONBIO, &block);
    }

    Py_INCREF(Py_None);
    return Py_None;
}
PyDoc_STRVAR(msbt_setblocking_doc, "");

static PyObject *
msbt_settimeout(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    double secondTimeout = -1;
    DWORD timeout = -1;
    int timeoutLen = sizeof(DWORD);

    if(!PyArg_ParseTuple(args, "id", &sockfd, &secondTimeout)) return 0;

    timeout = (DWORD) (secondTimeout * 1000);

    if(setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, 
                timeoutLen) != 0) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

    if(setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, (char*)&timeout, 
                timeoutLen) != 0) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

    Py_INCREF(Py_None);
    return Py_None;
}
PyDoc_STRVAR(msbt_settimeout_doc, "");

static PyObject *
msbt_gettimeout(PyObject *self, PyObject *args)
{
    int sockfd = -1;
    DWORD recv_timeout = -1;
    int recv_timeoutLen = sizeof(DWORD);
    double timeout = -1;

    if(!PyArg_ParseTuple(args, "i", &sockfd)) return 0;

    if(getsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&recv_timeout, 
                &recv_timeoutLen) != 0) {
        Err_SetFromWSALastError( PyExc_IOError );
        return 0;
    }

    timeout = (double)recv_timeout / 1000;

    return PyFloat_FromDouble(timeout);
}
PyDoc_STRVAR(msbt_gettimeout_doc, "");



// =======================  ADMINISTRATIVE =========================

static PyMethodDef msbt_methods[] = {
    { "initwinsock", (PyCFunction)msbt_initwinsock, METH_NOARGS, 
        msbt_initwinsock_doc },
    { "socket", (PyCFunction)msbt_socket, METH_VARARGS, msbt_socket_doc },
    { "bind", (PyCFunction)msbt_bind, METH_VARARGS, msbt_bind_doc },
    { "listen", (PyCFunction)msbt_listen, METH_VARARGS, msbt_listen_doc },
    { "accept", (PyCFunction)msbt_accept, METH_VARARGS, msbt_accept_doc },
    { "connect", (PyCFunction)msbt_connect, METH_VARARGS, msbt_connect_doc },
    { "send", (PyCFunction)msbt_send, METH_VARARGS, msbt_send_doc },
    { "recv", (PyCFunction)msbt_recv, METH_VARARGS, msbt_recv_doc },
    { "close", (PyCFunction)msbt_close, METH_VARARGS, msbt_close_doc },
    { "getsockname", (PyCFunction)msbt_getsockname, METH_VARARGS, 
        msbt_getsockname_doc },
    { "dup", (PyCFunction)msbt_dup, METH_VARARGS, msbt_dup_doc },
    { "discover_devices", (PyCFunction)msbt_discover_devices, METH_VARARGS, msbt_discover_devices_doc },
    { "lookup_name", (PyCFunction)msbt_lookup_name, METH_VARARGS, msbt_lookup_name_doc },
    { "find_service", (PyCFunction)msbt_find_service, METH_VARARGS, msbt_find_service_doc },
    { "set_service", (PyCFunction)msbt_set_service, METH_VARARGS, msbt_set_service_doc },
    { "set_service_raw", (PyCFunction)msbt_set_service_raw, METH_VARARGS, msbt_set_service_raw_doc },
    { "setblocking", (PyCFunction)msbt_setblocking, METH_VARARGS, msbt_setblocking_doc },
    { "settimeout", (PyCFunction)msbt_settimeout, METH_VARARGS, msbt_settimeout_doc },
    { "gettimeout", (PyCFunction)msbt_gettimeout, METH_VARARGS, msbt_gettimeout_doc },
    { NULL, NULL }
};

PyDoc_STRVAR(msbt_doc, "TODO\n");

#define ADD_INT_CONSTANT(m,a) PyModule_AddIntConstant(m, #a, a)

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC
init_msbt(void)
{
    PyObject * m = Py_InitModule3("_msbt", msbt_methods, msbt_doc);

    ADD_INT_CONSTANT(m, SOCK_STREAM);
    ADD_INT_CONSTANT(m, BTHPROTO_RFCOMM);
    ADD_INT_CONSTANT(m, BT_PORT_ANY);
}
#else
PyMODINIT_FUNC
PyInit__msbt(void)
{
    PyObject *m;

    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "_msbt",
        NULL,
        -1,
        msbt_methods,
        NULL,
        NULL,
        NULL,
        NULL
    };
    m = PyModule_Create(&moduledef);
#define ADD_INT_CONSTANT(m,a) PyModule_AddIntConstant(m, #a, a)

    ADD_INT_CONSTANT(m, SOCK_STREAM);
    ADD_INT_CONSTANT(m, BTHPROTO_RFCOMM);
    ADD_INT_CONSTANT(m, BT_PORT_ANY);
    return m;
}
#endif
