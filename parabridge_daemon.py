#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

import sys
import argparse
import threading
import time
import socket
import os
import json
import re
from SimpleXMLRPCServer import SimpleXMLRPCServer

class Config( object ) :

  m_oInstance = None
  m_oTimeReloadLast = None

  def __new__( i_oClass ) :
    if not i_oClass.m_oInstance :
      i_oClass.m_oInstance = super( Config, i_oClass ).__new__( i_oClass )
    return i_oClass.m_oInstance

  def __init__( self ) :
    self.m_mItems = { 'tasks' : [] }
    self.reload()

  def reload( self ) :
    sPath = os.path.expanduser( "~/.parabridge" )
    if os.path.exists( sPath ) :
      self.m_mItems.update( json.load( open( sPath ) ) )
      self.m_oTimeReloadLast = time.localtime()

  def timeReloadLast( self ) : return self.m_oTimeReloadLast

class Worker( threading.Thread ) :

  m_oInstance = None

  def __new__( i_oClass ) :
    if not i_oClass.m_oInstance :
      i_oClass.m_oInstance = super( Worker, i_oClass ).__new__( i_oClass )
    return i_oClass.m_oInstance

  def run( self ) :
    self.m_fShutdown = False
    while not self.m_fShutdown :
      time.sleep( 1 )

  def shutdown( self ) :
    self.m_fShutdown = True

class Server( SimpleXMLRPCServer, object ) :

  def __init__( self, i_nPort ) :
    gAddr = ( 'localhost', i_nPort )
    super( Server, self ).__init__( gAddr, logRequests = False )
    self.fShutdown = False
    self.register_function( self.stop )
    self.register_function( self.status )

  def serve_forever( self ) :
    while not self.fShutdown :
      self.handle_request()

  def stop( self ) :
    self.fShutdown = True
    return True

  def status( self ) :
    sMsg = """Daemon is running.
      \tConfiguration reloaded: {0}""".format(
      time.strftime( '%Y.%m.%d %H:%M:%S', Config().timeReloadLast() ) )
    return re.sub( '\t', ' ', re.sub( ' +', ' ', sMsg ) )

  def cfg_changed( self ) :
    Config().reload()

oParser = argparse.ArgumentParser( description = "Parabridge daemon" )
oParser.add_argument( 'port', type = int, help = "Port to listen on" )
oArgs = oParser.parse_args()
Worker().start()
try :
  Server( oArgs.port ).serve_forever()
except socket.error :
  ##  Unable to bind to port if already started.
  pass
finally :
  Worker().shutdown()

