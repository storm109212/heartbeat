#!/usr/bin/python

'''CTS: Cluster Testing System: Tests module

There are a few things we want to do here:

 '''

__copyright__='''
Copyright (C) 2000, 2001 Alan Robertson <alanr@unix.sh>
Licensed under the GNU GPL.

Add RecourceRecover testcase Zhao Kai <zhaokai@cn.ibm.com>
'''

#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#
#        SPECIAL NOTE:
#
#        Tests may NOT implement any cluster-manager-specific code in them.
#        EXTEND the ClusterManager object to provide the base capabilities
#        the test needs if you need to do something that the current CM classes
#        do not.  Otherwise you screw up the whole point of the object structure
#        in CTS.
#
#                Thank you.
#

import CTS
from CM_hb import HBConfig
import CTSaudits
import time, os, re, types, string, tempfile, sys
from CTSaudits import *
from stat import *

#        List of all class objects for tests which we ought to
#        consider running.

class RandomTests:
    '''
    A collection of tests which are run at random.
    '''
    def __init__(self, scenario, cm, tests, Audits):

        self.CM = cm
        self.Env = cm.Env
        self.Scenario = scenario
        self.Tests = []
        self.Audits = []
        self.ns=CTS.NodeStatus(self.Env)

        for test in tests:
            if not issubclass(test.__class__, CTSTest):
                raise ValueError("Init value must be a subclass of CTSTest")
            if test.is_applicable():
                self.Tests.append(test)

        if not scenario.IsApplicable():
                raise ValueError("Scenario not applicable in"
                " given Environment")

       
        self.Stats = {"success":0, "failure":0, "BadNews":0}
        self.IndividualStats= {}

        for audit in Audits:
            if not issubclass(audit.__class__, ClusterAudit):
                raise ValueError("Init value must be a subclass of ClusterAudit")
            if audit.is_applicable():
                self.Audits.append(audit)
        
    def incr(self, name):
        '''Increment (or initialize) the value associated with the given name'''
        if not self.Stats.has_key(name):
            self.Stats[name]=0
        self.Stats[name] = self.Stats[name]+1

    def audit(self, BadNews, test):
            errcount=0
            BadNewsDebug=0
            #BadNews.debug=1
            ignorelist = []                
            ignorelist.append(" CTS: ")
            ignorelist.append("BadNews:")
            ignorelist.extend(self.CM.errorstoignore())

            if test:
                ignorelist.extend(test.errorstoignore())

            while errcount < 1000:
                if BadNewsDebug: print "Looking for BadNews"
                match=BadNews.look(0)
                if match:
                   if BadNewsDebug: print "BadNews found: "+match
                   add_err = 1
                   for ignore in ignorelist:
                       if add_err == 1 and re.search(ignore, match):
                           if BadNewsDebug: print "Ignoring based on pattern: ("+ignore+")"
                           add_err = 0
                   if add_err == 1:
                       self.CM.log("BadNews: " + match)
                       self.incr("BadNews")
                       errcount=errcount+1
                else:
                  break
            else:
              self.CM.log("Big problems.  Shutting down.")
              self.CM.stopall()
              self.summarize()
              raise ValueError("Looks like we hit the jackpot!        :-)")

            for audit in self.Audits:
                if not audit():
                    self.CM.log("Audit " + audit.name() + " FAILED.")
                    self.incr("auditfail")
                    if test:
                        test.incr("auditfail")

    def summarize(self):
        self.CM.log("****************")
        self.CM.log("Overall Results:" + repr(self.Stats))
        self.CM.log("****************")
        self.CM.log("Detailed Results")
        for test in self.Tests:
            self.CM.log("Test %s: \t%s" %(test.name, repr(test.Stats)))
        self.CM.log("<<<<<<<<<<<<<<<< TESTS COMPLETED")

    def run(self, max=1):
        (
'''
Set up the given scenario, then run the selected tests at
random for the selected number of iterations.
''')
        BadNews=CTS.LogWatcher(self.CM["LogFileName"], self.CM["BadRegexes"]
        ,        timeout=0)
        BadNews.setwatch()

        self.CM.ns.WaitForAllNodesToComeUp(self.CM.Env["nodes"])

        for node in self.CM.Env["nodes"]:
            if node in self.CM.Env["oprofile"]:
                self.CM.log("Enabling oprofile on %s" % node) 
                self.CM.rsh.remote_py(node, "os", "system", "opcontrol --init")
                self.CM.rsh.remote_py(node, "os", "system", "opcontrol --start")

        if not self.Scenario.SetUp(self.CM):
            return None

        for node in self.CM.Env["nodes"]:
            if node in self.CM.Env["oprofile"]:
                self.CM.rsh.remote_py(
                    node, "os", "system", "opcontrol --save=cts.setup")

        testcount=1
        time.sleep(30)

        # This makes sure everything is stabilized before starting...
        self.audit(BadNews, None)

        while testcount <= max:
            test = self.Env.RandomGen.choice(self.Tests)

            # Some tests want a node as an argument.

            nodechoice = self.Env.RandomNode()
            #logsize = os.stat(self.CM["LogFileName"])[ST_SIZE]
            #self.CM.log("Running test %s (%s) \t[%d : %d]"  
            #            % (test.name, nodechoice, testcount, logsize))
            self.CM.log("Running test %s (%s) \t[%d]"  
                        % (test.name, nodechoice, testcount))

            testcount = testcount + 1
            starttime=time.time()
            test.starttime=starttime
            ret=test(nodechoice)

            for node in self.CM.Env["nodes"]:
                if node in self.CM.Env["oprofile"]:
                    self.CM.rsh.remote_py(
                        node, "os", "system", 
                        "opcontrol --save=cts.%d" % (testcount-1))

            if not self.CM.ns.WaitForAllNodesToComeUp(self.CM.Env["nodes"]):
              if os.path.isfile("./RecoverFromDeadNode"):
                self.CM.log("Calling ./RecoverFromDeadNode in an attempt to get things going again.")
                os.system("./RecoverFromDeadNode")
              if not self.CM.ns.WaitForAllNodesToComeUp(self.CM.Env["nodes"]):
                self.CM.log("One or more nodes will not come up - exiting")
                break

            if ret:
                self.incr("success")
            else:
                self.incr("failure")
                self.CM.log("Test %s (%s) \t[FAILED]" %(test.name,nodechoice))
                # Better get the current info from the cluster...
                self.CM.statall()
                # Make sure logging is working and we have enough disk space...
                if not self.CM.Env["DoBSC"]:
                    if not self.CM.TestLogging():
                        sys.exit(1)
                    if not self.CM.CheckDf():
                        sys.exit(1)
            stoptime=time.time()
            elapsed_time = stoptime - starttime
            test_time = stoptime - test.starttime
            if not test.has_key("min_time"):
                test["elapsed_time"] = elapsed_time
                test["min_time"] = test_time
                test["max_time"] = test_time
            else:
                test["elapsed_time"] = test["elapsed_time"] + elapsed_time
                if test_time < test["min_time"]:
                    test["min_time"] = test_time
                if test_time > test["max_time"]:
                    test["max_time"] = test_time
               
            self.audit(BadNews, test)

        self.Scenario.TearDown(self.CM)
        
        for node in self.CM.Env["nodes"]:
            if node in self.CM.Env["oprofile"]:
                self.CM.log("Disabling oprofile on %s" % node) 
                self.CM.rsh.remote_py(node, "os", "system", "opcontrol --shutdown")

        self.audit(BadNews, None)

        for test in self.Tests:
            self.IndividualStats[test.name] = test.Stats

        return self.Stats, self.IndividualStats

AllTestClasses = [ ]

class CTSTest:
    '''
    A Cluster test.
    We implement the basic set of properties and behaviors for a generic
    cluster test.

    Cluster tests track their own statistics.
    We keep each of the kinds of counts we track as separate {name,value}
    pairs.
    '''

    def __init__(self, cm):
        #self.name="the unnamed test"
        self.Stats = {"calls":0
        ,        "success":0
        ,        "failure":0
        ,        "skipped":0
        ,        "auditfail":0}

#        if not issubclass(cm.__class__, ClusterManager):
#            raise ValueError("Must be a ClusterManager object")
        self.CM = cm
        self.timeout=120
        self.starttime=0

    def has_key(self, key):
        return self.Stats.has_key(key)

    def __setitem__(self, key, value):
        self.Stats[key] = value
        
    def __getitem__(self, key):
        return self.Stats[key]

    def incr(self, name):
        '''Increment (or initialize) the value associated with the given name'''
        if not self.Stats.has_key(name):
            self.Stats[name]=0
        self.Stats[name] = self.Stats[name]+1

    def failure(self, reason="none"):
        '''Increment the failure count'''
        self.incr("failure")
        self.CM.log("Test " + self.name + " failed [reason:" + reason + "]")
        return None

    def success(self):
        '''Increment the success count'''
        self.incr("success")
        return 1

    def skipped(self):
        '''Increment the skipped count'''
        self.incr("skipped")
        return 1

    def __call__(self, node):
        '''Perform the given test'''
        raise ValueError("Abstract Class member (__call__)")
        self.incr("calls")
        return self.failure()

    def is_applicable(self):
        '''Return TRUE if we are applicable in the current test configuration'''
        raise ValueError("Abstract Class member (is_applicable)")
        return 1

    def canrunnow(self):
        '''Return TRUE if we can meaningfully run right now'''
        return 1

    def errorstoignore(self):
        '''Return list of errors which are 'normal' and should be ignored'''
        return []

###################################################################
class StopTest(CTSTest):
###################################################################
    '''Stop (deactivate) the cluster manager on a node'''
    def __init__(self, cm):
        CTSTest.__init__(self, cm)
        self.name="Stop"
        self.uspat   = self.CM["Pat:We_stopped"]
        self.thempat = self.CM["Pat:They_stopped"]

    def __call__(self, node):
        '''Perform the 'stop' test. '''
        self.incr("calls")
        if self.CM.ShouldBeStatus[node] != self.CM["up"]:
            return self.skipped()

        patterns = []
        # Technically we should always be able to notice ourselves stopping
        patterns.append(self.CM["Pat:We_stopped"] % node)

        if self.CM.Env["use_logd"]:
            patterns.append(self.CM["Pat:Logd_stopped"] % node)

        # Any active node needs to notice this one left
        # NOTE: This wont work if we have multiple partitions
        for other in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[other] == self.CM["up"] and other != node:
                patterns.append(self.CM["Pat:They_stopped"] %(other, node))
                #self.debug("Checking %s will notice %s left"%(other, node))
                
        watch = CTS.LogWatcher(
            self.CM["LogFileName"], patterns, self.CM["DeadTime"])
        watch.setwatch()

        if node == self.CM.OurNode:
            self.incr("us")
        else:
            if self.CM.upcount() <= 1:
                self.incr("all")
            else:
                self.incr("them")

        self.CM.StopaCM(node)
        watch_result = watch.lookforall()

        failreason=None
        UnmatchedList = "||"
        if watch.unmatched:
            for regex in watch.unmatched:
                self.CM.log ("ERROR: Shutdown pattern not found: %s" % (regex))
                UnmatchedList +=  regex + "||";
                failreason="Missing shutdown pattern"

        self.CM.cluster_stable(self.CM["DeadTime"])

        if not watch.unmatched or self.CM.upcount() == 0:
            return self.success()
        elif len(watch.unmatched) >= self.CM.upcount():
            return self.failure("no match against (%s)" % UnmatchedList)

        if failreason == None:
            return self.success()
        else:
            return self.failure(failreason)
#
# We don't register StopTest because it's better when called by
# another test...
#

###################################################################
class StartTest(CTSTest):
###################################################################
    '''Start (activate) the cluster manager on a node'''
    def __init__(self, cm, debug=None):
        CTSTest.__init__(self,cm)
        self.name="start"
        self.debug = debug
        self.uspat   = self.CM["Pat:We_started"]
        self.thempat = self.CM["Pat:They_started"]

    def __call__(self, node):
        '''Perform the 'start' test. '''
        self.incr("calls")

        if self.CM.upcount() == 0:
            self.incr("us")
        else:
            self.incr("them")

        if self.CM.ShouldBeStatus[node] != self.CM["down"]:
            return self.skipped()
        elif self.CM.StartaCM(node):
            return self.success()
        else:
            return self.failure("Startup %s on node %s failed"
                                %(self.CM["Name"], node))

    def is_applicable(self):
        '''StartTest is always applicable'''
        return 1
#
# We don't register StartTest because it's better when called by
# another test...
#

###################################################################
class FlipTest(CTSTest):
###################################################################
    '''If it's running, stop it.  If it's stopped start it.
       Overthrow the status quo...
    '''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="Flip"
        self.start = StartTest(cm)
        self.stop = StopTest(cm)

    def __call__(self, node):
        '''Perform the 'Flip' test. '''
        self.incr("calls")
        if self.CM.ShouldBeStatus[node] == self.CM["up"]:
            self.incr("stopped")
            ret = self.stop(node)
            type="up->down"
            # Give the cluster time to recognize it's gone...
            time.sleep(self.CM["StableTime"])
        elif self.CM.ShouldBeStatus[node] == self.CM["down"]:
            self.incr("started")
            ret = self.start(node)
            type="down->up"
        else:
            return self.skipped()

        self.incr(type)
        if ret:
            return self.success()
        else:
            return self.failure("%s failure" % type)

    def is_applicable(self):
        '''FlipTest is always applicable'''
        return 1

#        Register FlipTest as a good test to run
AllTestClasses.append(FlipTest)

###################################################################
class RestartTest(CTSTest):
###################################################################
    '''Stop and restart a node'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="Restart"
        self.start = StartTest(cm)
        self.stop = StopTest(cm)

    def __call__(self, node):
        '''Perform the 'restart' test. '''
        self.incr("calls")

        self.incr("node:" + node)
        
        ret1 = 1
        if self.CM.StataCM(node):
            self.incr("WasStopped")
            if not self.start(node):
                return self.failure("start (setup) failure: "+node)

        self.starttime=time.time()
        if not self.stop(node):
            return self.failure("stop failure: "+node)
        if not self.start(node):
            return self.failure("start failure: "+node)
        return self.success()

    def is_applicable(self):
        '''RestartTest is always applicable'''
        return 1

#        Register RestartTest as a good test to run
AllTestClasses.append(RestartTest)

###################################################################
class StonithTest(CTSTest):
###################################################################
    '''Reboot a node by whacking it with stonith.'''
    def __init__(self, cm, timeout=900):
        CTSTest.__init__(self,cm)
        self.name="Stonith"
        self.theystopped  = self.CM["Pat:They_dead"]
        self.allstopped   = self.CM["Pat:All_stopped"]
        self.usstart      = self.CM["Pat:We_started"]
        self.themstart    = self.CM["Pat:They_started"]
        self.timeout      = timeout
        self.ssherror     = False
    
    def _reset(self, node):
        StonithWorked=False
        for tries in 1,2,3,4,5:
          if self.CM.Env.ResetNode(node):
            StonithWorked=True
            break
        return StonithWorked

    def setup(self, target_node):
        # nothing to do
        return 1

    def __call__(self, node):
        '''Perform the 'stonith' test. (whack the node)'''
        self.incr("calls")
        stopwatch = 0
        rc = 0

        if not self.setup(node):
            return self.failure("Setup failed")

        # Figure out what log message to look for when/if it goes down
        #
        # Any active node needs to notice this one left
        # NOTE: This wont work if we have multiple partitions
        stop_patterns = []
        for other in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[other] == self.CM["up"] and other != node:
                stop_patterns.append(self.CM["Pat:They_stopped"] %(other, node))
                stopwatch = 1
                #self.debug("Checking %s will notice %s left"%(other, node))

        if self.CM.ShouldBeStatus[node] == self.CM["down"]:
            # actually no-one will notice this node die since HA isnt running
            stopwatch = 0

        #        Figure out what log message to look for when it comes up
        if self.CM.upcount() == 1 and self.CM.ShouldBeStatus[node] == self.CM["up"]:
            uppat = (self.usstart % node)
        else:
            uppat = (self.themstart % node)

        upwatch = CTS.LogWatcher(self.CM["LogFileName"], [uppat]
        ,        timeout=self.timeout)

        if stopwatch == 1:
            watch = CTS.LogWatcher(self.CM["LogFileName"], stop_patterns
            ,        timeout=self.CM["DeadTime"]+10)
            watch.setwatch()

        #        Reset (stonith) the node

        self.CM.debug("Resetting: "+node)
        StonithWorked = self._reset(node)

        if not StonithWorked:
            return self.failure("Stonith didn't work")
        if self.ssherror == True:
            self.CM.log("NOTE: Stonith command reported success but node %s did not restart (atd, reboot or ssh error)" % node)
            return self.success()

        upwatch.setwatch()

        #        Look() and see if the machine went down
        if stopwatch == 0:
            # Allow time for the node to die
            time.sleep(self.CM["DeadTime"]+10)
        elif not watch.lookforall():
            if watch.unmatched:
                for regex in watch.unmatched:
                    self.CM.log("Warn: STONITH pattern not found: %s"%regex)
                # !!no-one!! saw this node die
                if len(watch.unmatched) == len(stop_patterns):
                    return self.failure("No-one saw %s die" %node)
                # else: syslog* lost a message

        # Alas I dont think this check is plausable (beekhof)
        #
        # Check it really stopped...
        #self.CM.ShouldBeStatus[node] = self.CM["down"]
        #if self.CM.StataCM(node) == 1:
        #    ret1=0

        #        Look() and see if the machine came back up
        rc=0
        if upwatch.look():
            self.CM.debug("Startup pattern found: %s" %uppat)
            rc=1
        else:
            self.CM.log("Warn: Startup pattern not found: %s" %uppat)

        # Check it really started...
        self.CM.ShouldBeStatus[node] = self.CM["up"]
        if rc == 0 and self.CM.StataCM(node) == 1:
            rc=1

        # wait for the cluster to stabilize
        self.CM.cluster_stable()

        if node in self.CM.Env["oprofile"]:
            self.CM.log("Enabling oprofile on %s" % node) 
            self.CM.rsh.remote_py(node, "os", "system", "opcontrol --init")
            self.CM.rsh.remote_py(node, "os", "system", "opcontrol --start")

        # return case processing
        if rc == 0:
            return self.failure("Node %s did not restart" %node)
        else:
            return self.success()

    def is_applicable(self):
        '''StonithTest is applicable unless suppressed by CM.Env["DoStonith"] == FALSE'''

        # for v2, stonithd test is a better test to run.
        if self.CM["Name"] == "linux-ha-v2":
            return None
        if self.CM.Env.has_key("DoStonith"):
            return self.CM.Env["DoStonith"]
        return 1

#        Register StonithTest as a good test to run
AllTestClasses.append(StonithTest)


###################################################################
class StonithdTest(StonithTest):
###################################################################
    def __init__(self, cm, timeout=600):
        StonithTest.__init__(self, cm, timeout=600)
        self.name="Stonithd"
        self.startall = SimulStartLite(cm)
        self.start = StartTest(cm)
        self.stop = StopTest(cm)
        self.init_node = None

    def _reset(self, target_node):

        if len(self.CM.Env["nodes"]) < 2:
            return self.skipped()

        StonithWorked = False
        SshNotWork = 0
        for tries in range(1,5):
            # For some unknown reason, every now and then the ssh plugin just
            # can't kill the target_node - everything works fine with stonithd
            # and the plugin, but atd, reboot or ssh (or maybe something else)
            # doesn't do its job and target_node remains alive.  So look for
            # the indicative messages and bubble-up the error via ssherror
            watchpats = []
            watchpats.append("Initiating ssh-reset")
            watchpats.append("CRIT: still able to ping")
                
            watch = CTS.LogWatcher(self.CM["LogFileName"], watchpats
            ,     timeout=self.CM["DeadTime"]+60)
            watch.setwatch()
        
            fail_reasons = []
            if self.CM.Env.ResetNode2(self.init_node, target_node, fail_reasons):
                StonithWorked = True
                break
            if watch.lookforall():
                SshNotWork = SshNotWork + 1
                continue
            for reason in fail_reasons:
                self.CM.log(reason)

        if StonithWorked == False and SshNotWork == tries:
            StonithWorked = True
            self.ssherror = True

        return StonithWorked

    def setup(self, target_node):
        if len(self.CM.Env["nodes"]) < 2:
            return 1

        self.init_node = self.CM.Env.RandomNode()
        while self.init_node == target_node:
            self.init_node = self.CM.Env.RandomNode()

        if not self.startall(None):
            return self.failure("Test setup failed")

        return 1
        
    def is_applicable(self):

        if not self.CM["Name"] == "linux-ha-v2":
            return 0

        if self.CM.Env.has_key("DoStonith"):
            return self.CM.Env["DoStonith"]

        return 1
           
AllTestClasses.append(StonithdTest)

###################################################################
class IPaddrtest(CTSTest):
###################################################################
    '''Find the machine supporting a particular IP address, and knock it down.

    [Hint:  This code isn't finished yet...]
    '''

    def __init__(self, cm, IPaddrs):
        CTSTest.__init__(self,cm)
        self.name="IPaddrtest"
        self.IPaddrs = IPaddrs

        self.start = StartTest(cm)
        self.stop = StopTest(cm)

    def __call__(self, IPaddr):
        '''
        Perform the IPaddr test...
        '''
        self.incr("calls")

        node = self.CM.Env.RandomNode()
        self.incr("node:" + node)

        if self.CM.ShouldBeStatus[node] == self.CM["down"]:
            self.incr("WasStopped")
            self.start(node)

        ret1 = self.stop(node)
        # Give the cluster time to recognize we're gone...
        time.sleep(self.CM["StableTime"])
        ret2 = self.start(node)


        if not ret1:
            return self.failure("Could not stop")
        if not ret2:
            return self.failure("Could not start")

        return self.success()

    def is_applicable(self):
        '''IPaddrtest is always applicable (but shouldn't be)'''
        return 1

###################################################################
class StartOnebyOne(CTSTest):
###################################################################
    '''Start all the nodes ~ one by one'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="StartOnebyOne"
        self.stopall = SimulStopLite(cm)
        self.start = StartTest(cm)
        self.ns=CTS.NodeStatus(cm.Env)

    def __call__(self, dummy):
        '''Perform the 'StartOnebyOne' test. '''
        self.incr("calls")

        #        We ignore the "node" parameter...

        #        Shut down all the nodes...
        ret = self.stopall(None)
        if not ret:
            return self.failure("Test setup failed")

        failed=[]
        self.starttime=time.time()
        for node in self.CM.Env["nodes"]:
            if not self.start(node):
                failed.append(node)

        if len(failed) > 0:
            return self.failure("Some node failed to start: " + repr(failed))

        return self.success()

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        '''StartOnebyOne is always applicable'''
        return 1

#        Register StartOnebyOne as a good test to run
AllTestClasses.append(StartOnebyOne)

###################################################################
class SimulStart(CTSTest):
###################################################################
    '''Start all the nodes ~ simultaneously'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="SimulStart"
        self.stopall = SimulStopLite(cm)
        self.startall = SimulStartLite(cm)

    def __call__(self, dummy):
        '''Perform the 'SimulStart' test. '''
        self.incr("calls")

        #        We ignore the "node" parameter...

        #        Shut down all the nodes...
        ret = self.stopall(None)
        if not ret:
            return self.failure("Setup failed")
        
        self.CM.clear_all_caches()
 
        if not self.startall(None):
            return self.failure("Startall failed")

        return self.success()

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        '''SimulStart is always applicable'''
        return 1

#        Register SimulStart as a good test to run
AllTestClasses.append(SimulStart)

###################################################################
class SimulStop(CTSTest):
###################################################################
    '''Stop all the nodes ~ simultaneously'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="SimulStop"
        self.startall = SimulStartLite(cm)
        self.stopall = SimulStopLite(cm)

    def __call__(self, dummy):
        '''Perform the 'SimulStop' test. '''
        self.incr("calls")

        #     We ignore the "node" parameter...

        #     Start up all the nodes...
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")

        if not self.stopall(None):
            return self.failure("Stopall failed")

        return self.success()

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        '''SimulStop is always applicable'''
        return 1

#     Register SimulStop as a good test to run
AllTestClasses.append(SimulStop)

###################################################################
class StopOnebyOne(CTSTest):
###################################################################
    '''Stop all the nodes in order'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="StopOnebyOne"
        self.startall = SimulStartLite(cm)
        self.stop = StopTest(cm)

    def __call__(self, dummy):
        '''Perform the 'StopOnebyOne' test. '''
        self.incr("calls")

        #     We ignore the "node" parameter...

        #     Start up all the nodes...
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")

        failed=[]
        self.starttime=time.time()
        for node in self.CM.Env["nodes"]:
            if not self.stop(node):
                failed.append(node)

        if len(failed) > 0:
            return self.failure("Some node failed to stop: " + repr(failed))

        self.CM.clear_all_caches()
        return self.success()

    def is_applicable(self):
        '''StopOnebyOne is always applicable'''
        return 1

#     Register StopOnebyOne as a good test to run
AllTestClasses.append(StopOnebyOne)

###################################################################
class RestartOnebyOne(CTSTest):
###################################################################
    '''Restart all the nodes in order'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="RestartOnebyOne"
        self.startall = SimulStartLite(cm)

    def __call__(self, dummy):
        '''Perform the 'RestartOnebyOne' test. '''
        self.incr("calls")

        #     We ignore the "node" parameter...

        #     Start up all the nodes...
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")

        did_fail=[]
        self.starttime=time.time()
        self.restart = RestartTest(self.CM)
        for node in self.CM.Env["nodes"]:
            if not self.restart(node):
                did_fail.append(node)

        if did_fail:
            return self.failure("Could not restart %d nodes: %s" 
                                %(len(did_fail), repr(did_fail)))
        return self.success()

    def is_applicable(self):
        '''RestartOnebyOne is always applicable'''
        return 1

#     Register StopOnebyOne as a good test to run
AllTestClasses.append(RestartOnebyOne)

###################################################################
class PartialStart(CTSTest):
###################################################################
    '''Start a node - but tell it to stop before it finishes starting up'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="PartialStart"
        self.startall = SimulStartLite(cm)
        self.stopall = SimulStopLite(cm)

    def __call__(self, node):
        '''Perform the 'PartialStart' test. '''
        self.incr("calls")

        ret = self.stopall(None)
        if not ret:
            return self.failure("Setup failed")

#	FIXME!  This should use the CM class to get the pattern
#		then it would be applicable in general
        watchpats = []
        watchpats.append("Starting crmd")
        watch = CTS.LogWatcher(self.CM["LogFileName"], watchpats,
                               timeout=self.CM["DeadTime"]+10)
        watch.setwatch()

        self.CM.StartaCMnoBlock(node)
        ret = watch.lookforall()
        if not ret:
            self.CM.log("Patterns not found: " + repr(watch.unmatched))
            return self.failure("Setup of %s failed" % node) 

        ret = self.stopall(None)
        if not ret:
            return self.failure("%s did not stop in time" % node)

        return self.success()

    def is_applicable(self):
        '''Partial is always applicable'''
        if self.CM["Name"] == "linux-ha-v2":
          return 1
        else:
          return 0

#     Register StopOnebyOne as a good test to run
AllTestClasses.append(PartialStart)

###################################################################
class StandbyTest(CTSTest):
###################################################################
    '''Put a node in standby mode'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="standby"
        self.successpat          = self.CM["Pat:StandbyOK"]
        self.nostandbypat        = self.CM["Pat:StandbyNONE"]
        self.transient           = self.CM["Pat:StandbyTRANSIENT"]

    def __call__(self, node):
        '''Perform the 'standby' test. '''
        self.incr("calls")

        if self.CM.ShouldBeStatus[node] == self.CM["down"]:
            return self.skipped()

        if self.CM.upcount() < 2:
            self.incr("nostandby")
            pat = self.nostandbypat
        else:
            self.incr("standby")
            pat = self.successpat

        #
        # You could make a good argument that the cluster manager
        # ought to give us good clues on when its a bad time to
        # switch over to the other side, but heartbeat doesn't...
        # It could also queue the request.  But, heartbeat
        # doesn't do that either :-)
        #
        retrycount=0
        while (retrycount < 10):
            watch = CTS.LogWatcher(self.CM["LogFileName"]
            ,        [pat, self.transient]
            ,        timeout=self.CM["DeadTime"]+10)
            watch.setwatch()

            self.CM.rsh(node, self.CM["Standby"])

            match = watch.look()
            if match:
                if re.search(self.transient, match):
                    self.incr("retries")
                    time.sleep(2)
                    retrycount=retrycount+1
                else:
                    return self.success()
            else:
                break  # No point in retrying...
        return self.failure("did not find pattern " + pat)

    def is_applicable(self):
        '''StandbyTest is applicable when the CM has a Standby command'''

        if not self.CM.has_key("Standby"):
           return None
        else:

            #if self.CM.Env.has_key("DoStandby"):
                #flag=self.CM.Env["DoStandby"]
                #if type(flag) == types.IntType:
                    #return flag
                #if not re.match("[yt]", flag, re.I):
                    #return None
            #
            # We need to strip off everything after the first blank
            #
            cmd=self.CM["Standby"]
            cmd = cmd.split()[0]
            if not os.access(cmd, os.X_OK):
                return None

            cf = self.CM.cf
            if not cf.Parameters.has_key("auto_failback"):
                return None
            elif cf.Parameters["auto_failback"][0] == "legacy":
                return None
            return 1

#        Register StandbyTest as a good test to run
AllTestClasses.append(StandbyTest)


#######################################################################
class StandbyTest2(CTSTest):
#######################################################################
    '''Standby with CRM of HA release 2'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="standby2"
            
        self.start = StartTest(cm)
        self.startall = SimulStartLite(cm)
        
    # make sure the node is active
    # set the node to standby mode
    # check resources, none resource should be running on the node
    # set the node to active mode
    # check resouces, resources should have been migrated back (SHOULD THEY?)
    
    def __call__(self, node):
    
        self.incr("calls")
        ret=self.startall(None)
        if not ret:
            return self.failure("Start all nodes failed")
        
        self.CM.debug("Make sure node %s is active" % node)    
        if self.CM.StandbyStatus(node) != "off":
            if not self.CM.SetStandbyMode(node, "off"):
                return self.failure("can't set node %s to active mode" % node)
               
        self.CM.cluster_stable()

        status = self.CM.StandbyStatus(node)
        if status != "off":
            return self.failure("standby status of %s is [%s] but we expect [off]" % (node, status))

        self.CM.debug("Getting resources running on node %s" % node)
        rsc_on_node = []
        for rsc in self.CM.Resources():
            if rsc.IsRunningOn(node):
                rsc_on_node.append(rsc)

        self.CM.debug("Setting node %s to standby mode" % node) 
        if not self.CM.SetStandbyMode(node, "on"):
            return self.failure("can't set node %s to standby mode" % node)

        time.sleep(30)  # Allow time for the update to be applied and cause something
        self.CM.cluster_stable()

        status = self.CM.StandbyStatus(node)
        if status != "on":
            return self.failure("standby status of %s is [%s] but we expect [on]" % (node, status))

        self.CM.debug("Checking resources")
        for rsc in self.CM.Resources():
            if rsc.IsRunningOn(node):
                return self.failure("%s set to standby, %s is still running on it" % (node, rsc.rid))

        self.CM.debug("Setting node %s to active mode" % node) 
        if not self.CM.SetStandbyMode(node, "off"):
            return self.failure("can't set node %s to active mode" % node)

        time.sleep(30)  # Allow time for the update to be applied and cause something
        self.CM.cluster_stable()

        status = self.CM.StandbyStatus(node)
        if status != "off":
            return self.failure("standby status of %s is [%s] but we expect [off]" % (node, status))

        self.CM.debug("Checking resources")
        for rsc in rsc_on_node:
            if not rsc.IsRunningOn(node):
                return self.failure("%s set to active but %s is NOT back" % (node, rsc.rid))


        return self.success()

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2":
            return 1
        return 0

AllTestClasses.append(StandbyTest2)

#######################################################################
class Fastdetection(CTSTest):
#######################################################################
    '''Test the time which one node find out the other node is killed very quickly'''
    def __init__(self,cm,timeout=60):
        CTSTest.__init__(self, cm)
        self.name = "DetectionTime"
        self.they_stopped = self.CM["Pat:They_stopped"]
        self.timeout = timeout
        self.start = StartTest(cm)
        self.startall = SimulStartLite(cm)
        self.standby = StandbyTest(cm)
        self.__setitem__("min", 0)
        self.__setitem__("max", 0)
        self.__setitem__("totaltime", 0)

    def __call__(self, node):
        '''Perform the fastfailureDetection test'''
        self.incr("calls")

        ret=self.startall(None)
        if not ret:
            return self.failure("Test setup failed")

        if self.CM.upcount() < 2:
            return self.skipped()

        # Make sure they're not holding any resources
        ret = self.standby(node)
        if not ret:
            return ret

        stoppat = (self.they_stopped % ("", node))
        stopwatch = CTS.LogWatcher(self.CM["LogFileName"], [stoppat], timeout=self.timeout)
        stopwatch.setwatch()

#
#        This test is CM-specific - FIXME!!
#
        if self.CM.rsh(node, "killall -9 heartbeat")==0:
            Starttime = os.times()[4]
            if stopwatch.look():
                Stoptime = os.times()[4]
#        This test is CM-specific - FIXME!!
                self.CM.rsh(node, "killall -9 /usr/lib/heartbeat/ccm /usr/lib/heartbeat/ipfail >/dev/null 2>&1; true")
                Detectiontime = Stoptime-Starttime
                detectms = int(Detectiontime*1000+0.5)
                self.CM.log("...failure detection time: %d ms" % detectms)
                self.Stats["totaltime"] = self.Stats["totaltime"] + Detectiontime
                if self.Stats["min"] == 0:
                    self.Stats["min"] = Detectiontime
                if Detectiontime > self.Stats["max"]:
                    self.Stats["max"] = Detectiontime
                if Detectiontime < self.Stats["min"]:
                    self.Stats["min"] = Detectiontime
                self.CM.ShouldBeStatus[node] = self.CM["down"]
                self.start(node)
                return self.success()
            else:
#        This test is CM-specific - FIXME!!
                self.CM.rsh(node, "killall -9 /usr/lib/heartbeat/ccm /usr/lib/heartbeat/ipfail >/dev/null 2>&1; true")
                self.CM.ShouldBeStatus[node] = self.CM["down"]
                ret=self.start(node)
                return self.failure("Didn't find the log message")
        else:
            return self.failure("Couldn't kill cluster manager")

    def is_applicable(self):
        '''This test is applicable when auto_failback != legacy'''
        return self.standby.is_applicable()

#        This test is CM-specific - FIXME!!
    def errorstoignore(self):
        '''Return list of errors which are 'normal' and should be ignored'''
        return [ "ccm.*ERROR: ccm_control_process:failure to send protoversion request"
        ,        "ccm.*ERROR: Lost connection to heartbeat service. Need to bail out"
        ]

AllTestClasses.append(Fastdetection)

##############################################################################
class BandwidthTest(CTSTest):
##############################################################################
#        Tests should not be cluster-manager-specific
#        If you need to find out cluster manager configuration to do this, then
#        it should be added to the generic cluster manager API.
    '''Test the bandwidth which heartbeat uses'''
    def __init__(self, cm):
        CTSTest.__init__(self, cm)
        self.name = "Bandwidth"
        self.start = StartTest(cm)
        self.__setitem__("min",0)
        self.__setitem__("max",0)
        self.__setitem__("totalbandwidth",0)
        self.tempfile = tempfile.mktemp(".cts")
        self.startall = SimulStartLite(cm)
        
    def __call__(self, node):
        '''Perform the Bandwidth test'''
        self.incr("calls")
        
        if self.CM.upcount()<1:
            return self.skipped()

        Path = self.CM.InternalCommConfig()
        if "ip" not in Path["mediatype"]:
             return self.skipped()

        port = Path["port"][0]
        port = int(port)

        ret = self.startall(None)
        if not ret:
            return self.failure("Test setup failed")
        time.sleep(5)  # We get extra messages right after startup.


        fstmpfile = "/var/run/band_estimate"
        dumpcmd = "tcpdump -p -n -c 102 -i any udp port %d > %s 2>&1" \
        %                (port, fstmpfile)
 
        rc = self.CM.rsh(node, dumpcmd)
        if rc == 0:
            farfile = "root@%s:%s" % (node, fstmpfile)
            self.CM.rsh.cp(farfile, self.tempfile)
            Bandwidth = self.countbandwidth(self.tempfile)
            if not Bandwidth:
                self.CM.log("Could not compute bandwidth.")
                return self.success()
            intband = int(Bandwidth + 0.5)
            self.CM.log("...bandwidth: %d bits/sec" % intband)
            self.Stats["totalbandwidth"] = self.Stats["totalbandwidth"] + Bandwidth
            if self.Stats["min"] == 0:
                self.Stats["min"] = Bandwidth
            if Bandwidth > self.Stats["max"]:
                self.Stats["max"] = Bandwidth
            if Bandwidth < self.Stats["min"]:
                self.Stats["min"] = Bandwidth
            self.CM.rsh(node, "rm -f %s" % fstmpfile)
            os.unlink(self.tempfile)
            return self.success()
        else:
            return self.failure("no response from tcpdump command [%d]!" % rc)

    def countbandwidth(self, file):
        fp = open(file, "r")
        fp.seek(0)
        count = 0
        sum = 0
        while 1:
            line = fp.readline()
            if not line:
                return None
            if re.search("udp",line) or re.search("UDP,", line):
                count=count+1
                linesplit = string.split(line," ")
                for j in range(len(linesplit)-1):
                    if linesplit[j]=="udp": break
                    if linesplit[j]=="length:": break
                        
                try:
                    sum = sum + int(linesplit[j+1])
                except ValueError:
                    self.CM.log("Invalid tcpdump line: %s" % line)
                    return None
                T1 = linesplit[0]
                timesplit = string.split(T1,":")
                time2split = string.split(timesplit[2],".")
                time1 = (long(timesplit[0])*60+long(timesplit[1]))*60+long(time2split[0])+long(time2split[1])*0.000001
                break

        while count < 100:
            line = fp.readline()
            if not line:
                return None
            if re.search("udp",line) or re.search("UDP,", line):
                count = count+1
                linessplit = string.split(line," ")
                for j in range(len(linessplit)-1):
                    if linessplit[j] =="udp": break
                    if linesplit[j]=="length:": break
                try:
                    sum=int(linessplit[j+1])+sum
                except ValueError:
                    self.CM.log("Invalid tcpdump line: %s" % line)
                    return None

        T2 = linessplit[0]
        timesplit = string.split(T2,":")
        time2split = string.split(timesplit[2],".")
        time2 = (long(timesplit[0])*60+long(timesplit[1]))*60+long(time2split[0])+long(time2split[1])*0.000001
        time = time2-time1
        if (time <= 0):
            return 0
        return (sum*8)/time

    def is_applicable(self):
        '''BandwidthTest is always applicable'''
        return 0

AllTestClasses.append(BandwidthTest)

##########################################################################
class RedundantpathTest(CTSTest):
##########################################################################
    '''In heartbeat, it has redundant path to communicate between the cluster'''
#
#        Tests should not be cluster-manager specific
#        One needs to isolate what you need from the cluster manager and then
#        add a (new) API to do it.
#
    def __init__(self,cm,timeout=60):
        CTSTest.__init__(self,cm)
        self.name = "RedundantpathTest"
        self.timeout = timeout 

    def PathCount(self):
        '''Return number of communication paths'''
        Path = self.CM.InternalCommConfig()
        cf = self.CM.cf
        eths = []
        serials = []
        num = 0
        for interface in Path["interface"]:
            if re.search("eth",interface):
                eths.append(interface)
                num = num + 1
            if re.search("/dev",interface):
                serials.append(interface)
                num = num + 1

        return (num, eths, serials)

    def __call__(self,node):
        '''Perform redundant path test'''
        self.incr("calls")
        if self.CM.ShouldBeStatus[node]!=self.CM["up"]:
            return self.skipped()
    
        (num, eths, serials) = self.PathCount()

        for eth in eths:
            if self.CM.rsh(node,"ifconfig %s down" % eth)==0:
                PathDown = "OK"
                break
        
        if PathDown != "OK":
            for serial in serials:
                if self.CM.rsh(node,"setserial %s uart none" % serial)==0:
                    PathDown = "OK"
                    break
                   
        if PathDown != "OK":
            return self.failure("Cannot break the path")
        
        time.sleep(self.timeout)

        for audit in CTSaudits.AuditList(self.CM):
            if not audit():
                for eth in eths:
                    self.CM.rsh(node,"ifconfig %s up" % eth)
                for serial in serials:
                    self.CM.rsh(node,"setserial %s uart 16550" % serial) 
                return self.failure("Redundant path fail")

        for eth in eths:
            self.CM.rsh(node,"ifconfig %s up" % eth)
        for serial in serials:
            self.CM.rsh(node,"setserial %s uart 16550" % serial)
       
        return self.success()

    def is_applicable(self):
        '''It is applicable when you have more than one connection'''
        return self.PathCount()[0] > 1

# FIXME!!  Why is this one commented out?
#AllTestClasses.append(RedundantpathTest)

##########################################################################
class DRBDTest(CTSTest):
##########################################################################
    '''In heartbeat, it provides replicated storage.'''
    def __init__(self,cm, timeout=10):
        CTSTest.__init__(self,cm)
        self.name = "DRBD"
        self.timeout = timeout

    def __call__(self, dummy):
        '''Perform the 'DRBD' test.'''
        self.incr("calls")
        
        for node in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[node] == self.CM["down"]:
                return self.skipped()

        # Note:  All these special cases with Start/Stop/StatusDRBD
        # should be reworked to use resource objects instead of
        # being hardwired to bypass the objects here.

        for node in self.CM.Env["nodes"]:
            done=time.time()+self.timeout+1
            while (time.time()<done):
                 line=self.CM.rsh.readaline(node,self.CM["StatusDRBDCmd"])
                 if re.search("running",line):
                     break
                 else:
                      self.CM.rsh(node,self.CM["StartDRBDCmd"])
                      time.sleep(1)
            if time.time()>done:
                return self.failure("Can't start drbd, please check it") 

        device={}
        for node in self.CM.Env["nodes"]:
            device[node]=self.getdevice(node)

        node = self.CM.Env["nodes"][0]
        done=time.time()+self.timeout+1
        while 1:
            if (time.time()>done):
                return self.failure("the drbd could't sync")
            self.CM.rsh(node,"cp /proc/drbd /var/run >/dev/null 2>&1")
            if self.CM.rsh.cp("%s:/var/run/drbd" % node,"/var/run"):
                line = open("/tmp/var/run").readlines()[2]
                p = line.find("Primary")
                s1 = line.find("Secondary")
                s2 = line.rfind("Secondary")
                if s1!=s2:
                    if self.CM.rsh(node,"drbdsetup %s primary" % device[node]):
                       pass
                if p!=-1:
                    if p<s1:
                        primarynode = node
                        secondarynode = self.CM.Env["nodes"][1]
                        break
                else:
                    if s1!=-1:
                        primarynode = self.CM.Env["nodes"][1]
                        secondarynode = node
                        break
                time.sleep(1)
                 
        self.CM.rsh(secondarynode, self.CM["StopCmd"])
        self.CM.rsh(primarynode, self.CM["StopCmd"])

        line1 = self.CM.rsh.readaline(node,"md5sum %s" % device[primarynode])
        line2 = self.CM.rsh.readaline(node,"md5sum %s" % device[secondarynode])

        self.CM.rsh(primarynode,self.CM["StartCmd"])
        self.CM.rsh(secondarynode,self.CM["StartCmd"])

        if string.split(line1," ")[0] == string.split(line2, " "):
            return self.failure("Drbd desnt't work good")

        return self.success()

    def getdevice(self,node):
        device=None
        if self.CM.rsh(node,self.CM["DRBDCheckconf"])==0:
            self.CM.rsh.cp("%s:/var/run/drbdconf" % node, "/var/run")
            lines=open("/var/run/drbdconf","r")
            for line in lines:
                if line.find("%s:device" % node)!=-1:
                    device=string.split(line," ")[8]
                    break
        return device

    def is_applicable(self):
        '''DRBD is applicable when there are drbd devices'''

        for group in self.CM.ResourceGroups():
            for resource in group:
                if resource.Type() == "datadisk":
                    return 1
        return None

AllTestClasses.append(DRBDTest)

####################################################################
class Split_brainTest(CTSTest):
####################################################################
    '''It is used to test split-brain. when the path between the two nodes break
       check the two nodes both take over the resource'''
    def __init__(self,cm):
        CTSTest.__init__(self,cm)
        self.name = "Split_brain"
        self.start = StartTest(cm)
        self.startall = SimulStartLite(cm)

    def __call__(self, node):
        '''Perform split-brain test'''
        self.incr("calls")

        ret = self.startall(None)
        if not ret:
            return self.failure("Test setup failed")

        '''isolate node, Look for node is dead message'''
        watchstoppats = [ ]
        stoppat = self.CM["Pat:They_stopped"]
        for member in self.CM.Env["nodes"]:
            if member != node:
                thispat = (stoppat % (node,member))
                watchstoppats.append(thispat)
                thatpat = (stoppat % (member,node))
                watchstoppats.append(thatpat)

        watchstop = CTS.LogWatcher(self.CM["LogFileName"], watchstoppats\
        ,       timeout=self.CM["DeadTime"]+60)
        watchstop.ReturnOnlyMatch()

        watchstop.setwatch()
        if float(self.CM.Env["XmitLoss"])!=0 or float(self.CM.Env["RecvLoss"])!=0 :
            self.CM.savecomm_node(node)
        if not self.CM.isolate_node(node):
            return self.failure("Could not isolate the nodes")
        if not watchstop.lookforall():
            self.CM.unisolate_node(node)
            self.CM.log("Patterns not found: " + repr(watchstop.unmatched))
            return self.failure("Didn't find the log 'dead' message")

        '''
        Unisolate the node, look for the return partition message
        and check whether they restart
        '''
        watchpartitionpats = [ ]
        partitionpat = self.CM["Pat:Return_partition"]
        watchstartpats = [ ]
        startpat = self.CM["Pat:We_started"]

        for member in self.CM.Env["nodes"]:
            thispat = (partitionpat % member)
            thatpat = (startpat % member)
            watchpartitionpats.append(thispat)
            watchstartpats.append(thatpat)
        watchpartition = CTS.LogWatcher(self.CM["LogFileName"], watchpartitionpats\
        ,               timeout=self.CM["DeadTime"]+60)
        watchstart = CTS.LogWatcher(self.CM["LogFileName"], watchstartpats\
        ,                timeout=self.CM["DeadTime"]+60)
        watchstart.ReturnOnlyMatch()

        watchpartition.setwatch()
        watchstart.setwatch()
        
        self.CM.unisolate_node(node)
        if float(self.CM.Env["XmitLoss"])!=0 or float(self.CM.Env["RecvLoss"])!=0 :
            self.CM.restorecomm_node(node)

        if not watchpartition.lookforall():
            self.CM.log("Patterns not found: " + repr(watchpartition.unmatched))
            return self.failure("Didn't find return from partition messages")
        
        if not watchstart.lookforall():
            self.CM.log("Patterns not found: " + repr(watchstart.unmatched))
            return self.failure("Both nodes didn't restart")
        return self.success()

    def is_applicable(self):
        '''Split_brain is applicable for 1.X'''
        if self.CM["Name"] == "heartbeat":
            return 1
        return 0

#
#        FIXME!!  This test has hard-coded cluster-manager-specific things in it!!
#        
    def errorstoignore(self):
        '''Return list of errors which are 'normal' and should be ignored'''
        return [ "ERROR:.*Both machines own.*resources"
        ,        "ERROR:.*lost a lot of packets!"
        ,        "ERROR: Cannot rexmit pkt .*: seqno too low"
        ,        "ERROR: Irretrievably lost packet: node"
        ,        "CRIT: Cluster node .* returning after partition"
        ]

AllTestClasses.append(Split_brainTest)


###################################################################
class ResourceRecover(CTSTest):
###################################################################
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="ResourceRecover"
        self.start = StartTest(cm)
        self.startall = SimulStartLite(cm)
        self.max=30
        self.rid=None
        self.action = "fail"

        # make sure the interval is greater than 0 so failcount is updated
        self.interval = 60000

    def __call__(self, node):
        '''Perform the 'ResourceRecover' test. '''
        self.incr("calls")
        
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")

        resourcelist = self.CM.active_resources(node)
        # if there are no resourcelist, return directly
        if len(resourcelist)==0:
            self.CM.log("No active resources on %s" % node)
            return self.skipped()

        self.rid = self.CM.Env.RandomGen.choice(resourcelist)
        self.CM.debug("Shooting %s..." % self.rid)

        pats = []
        pats.append("crmd.* Performing op=%s_stop_0" % self.rid)
        pats.append("crmd.* Performing op=%s_start_0" % self.rid)
        pats.append("crmd.* LRM operation %s_start_0.*complete" % self.rid)
        pats.append("Updating failcount for %s on .* after .* %s"
                    % (self.rid, self.action))

        watch = CTS.LogWatcher(self.CM["LogFileName"], pats, timeout=60)
        watch.setwatch()
        
        # fail a resource by calling an action it doesn't support
        self.CM.rsh.remote_py(node, "os", "system",
                              "/usr/sbin/crm_resource -F -r %s -H %s &>/dev/null" % (self.rid, node))

        watch.lookforall()

        self.CM.cluster_stable()
        recovernode=self.CM.ResourceLocation(self.rid)

        if len(recovernode)==1:
            self.CM.debug("Recovered: %s is running on %s" 
                          %(self.rid, recovernode[0]))
            if not watch.unmatched: 
                return self.success()
            else:
                return self.failure("Patterns not found: %s" 
                                    % repr(watch.unmatched))

        elif len(recovernode)==0:
            return self.failure("%s was not recovered and is inactive" 
                                % self.rid)
        else:
            return self.failure("%s is now active on more than one node: %s"
                                %(self.rid, str(recovernode)))

    def is_applicable(self):
        '''ResourceRecover is applicable only when there are resources running
         on our cluster and environment is linux-ha-v2'''
        if self.CM["Name"] == "linux-ha-v2":
            resourcelist=self.CM.Resources()
            if len(resourcelist)==0:
                self.CM.log("No resources on this cluster")
                return 0
            else:
                return 1
        return 0
    
    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return [ """Updating failcount for %s""" % self.rid,
                 """Unknown operation: fail""",
                 """ERROR: sending stonithRA op to stonithd failed.""",
                 """ERROR: process_lrm_event: LRM operation %s_%s_%d""" % (self.rid, self.action, self.interval),
                 """ERROR: process_graph_event: Action %s_%s_%d initiated outside of a transition""" % (self.rid, self.action, self.interval),
                 ]

AllTestClasses.append(ResourceRecover)

###################################################################
class ComponentFail(CTSTest):
###################################################################
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="ComponentFail"
        self.startall = SimulStartLite(cm)
        self.complist = cm.Components()
        self.patterns = []
        self.okerrpatterns = []

    def __call__(self, node):
        '''Perform the 'ComponentFail' test. '''
        self.incr("calls")
        self.patterns = []
        self.okerrpatterns = []

        # start all nodes
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")

        if not self.CM.cluster_stable(self.CM["StableTime"]):
            return self.failure("Setup failed - unstable")

        node_is_dc = self.CM.is_node_dc(node, None)

        # select a component to kill
        chosen = self.CM.Env.RandomGen.choice(self.complist)
        while chosen.dc_only == 1 and node_is_dc == 0:
            chosen = self.CM.Env.RandomGen.choice(self.complist)

        self.CM.log("...component %s (dc=%d,boot=%d)" % (chosen.name, node_is_dc,chosen.triggersreboot))
        self.incr(chosen.name)
        
        self.patterns.extend(chosen.pats)

        # Make sure the node goes down and then comes back up if it should reboot...
        if chosen.triggersreboot:
          for other in self.CM.Env["nodes"]:
              if other != node:
                  self.patterns.append(self.CM["Pat:They_stopped"] %(other, node))
          self.patterns.append(self.CM["Pat:They_started"] % node)

        # In an ideal world, this next stuff should be in the "chosen" object as a member function
        if chosen.dc_only:
          if chosen.triggersreboot:
            # Sometimes these will be in the log, and sometimes they won't...
            self.okerrpatterns.append("%s crmd:.*Process %s:.* exited" %(node, chosen.name))
            self.okerrpatterns.append("%s crmd:.*I_ERROR.*crmdManagedChildDied" %node)
            self.okerrpatterns.append("%s crmd:.*The %s subsystem terminated unexpectedly" %(node, chosen.name))
            self.okerrpatterns.append("ERROR: Client .* exited with return code")
          else:
            self.patterns.append("%s crmd:.*Process %s:.* exited" %(node, chosen.name))
            self.patterns.append("%s crmd:.*I_ERROR.*crmdManagedChildDied" %node)
            self.patterns.append("%s crmd:.*The %s subsystem terminated unexpectedly" %(node, chosen.name))
        else:
          if chosen.triggersreboot:
            # Sometimes this won't be in the log...
            self.okerrpatterns.append("%s heartbeat.*%s.*killed by signal 9" %(node, chosen.name))
            self.okerrpatterns.append("%s heartbeat.*Respawning client " % (node))
            self.okerrpatterns.append("ERROR: Client .* exited with return code")
          else:
            self.patterns.append("%s heartbeat.*%s.*killed by signal 9" %(node, chosen.name))
            self.patterns.append("%s heartbeat.*Respawning client.*%s" %(node, chosen.name))
        if node_is_dc:
          self.patterns.extend(chosen.dc_pats)

        # supply a copy so self.patterns doesnt end up empty
        tmpPats = []
        tmpPats.extend(self.patterns)
        self.patterns.extend(chosen.badnews_ignore)

        # set the watch for stable
        watch = CTS.LogWatcher(
            self.CM["LogFileName"], tmpPats, 
            self.CM["DeadTime"] + self.CM["StableTime"] + self.CM["StartTime"])
        watch.setwatch()
        
        # kill the component
        chosen.kill(node)

        # check to see Heartbeat noticed
        matched = watch.lookforall()
        if not matched:
            self.CM.log("Patterns not found: " + repr(watch.unmatched))
            self.CM.cluster_stable(self.CM["StartTime"])
            return self.failure("Didn't find all expected patterns")
        
        self.CM.debug("Found: "+ repr(matched))

        # now watch it recover...
        for attempt in (1, 2, 3, 4, 5):
            self.CM.debug("Waiting for the cluster to recover...")
            if self.CM.cluster_stable(self.CM["StartTime"]):
                return self.success()

        return self.failure("Cluster did not become stable")

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2":
            return 1
        return 0
    
    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
	# Note that okerrpatterns refers to the last time we ran this test
	# The good news is that this works fine for us...
        self.okerrpatterns.extend(self.patterns)
        return self.okerrpatterns
    
AllTestClasses.append(ComponentFail)

####################################################################
class Split_brainTest2(CTSTest):
####################################################################
    '''It is used to test split-brain. when the path between the two nodes break
       check the two nodes both take over the resource'''
    def __init__(self,cm):
        CTSTest.__init__(self,cm)
        self.name = "Split_brain2"
        self.start = StartTest(cm)
        self.startall = SimulStartLite(cm)

    def __call__(self, node):
        '''Perform split-brain test'''
        self.incr("calls")
        ret = self.startall(None)
        if not ret:
            return self.failure("Setup failed")
        
        count1 = self.CM.Env.RandomGen.randint(1,len(self.CM.Env["nodes"])-1)
        partition1 = []
        while len(partition1) < count1:
            select = self.CM.Env.RandomGen.choice(self.CM.Env["nodes"])
            if not select in partition1:
                partition1.append(select)
        partition2 = []
        for member in self.CM.Env["nodes"]:
            if not member in partition1:
                partition2.append(member)
        allownodes1 = ""
        for member in partition1:
            allownodes1 += member + " "
        allownodes2 = ""
        for member in partition2:
            allownodes2 += member + " "
        self.CM.log("Partition1: " + str(partition1))
        self.CM.log("Partition2: " + str(partition2))

        '''isolate nodes, Look for node is dead message'''
        watchdeadpats = [ ]
        deadpat = self.CM["Pat:They_dead"]
        for member in self.CM.Env["nodes"]:
            thispat = (deadpat % member)
            watchdeadpats.append(thispat)

        watchdead = CTS.LogWatcher(self.CM["LogFileName"], watchdeadpats\
        ,       timeout=self.CM["DeadTime"]+60)
        watchdead.ReturnOnlyMatch()
        watchdead.setwatch()
        
        for member in partition1:
            if float(self.CM.Env["XmitLoss"])!=0 or float(self.CM.Env["RecvLoss"])!=0 :
                self.CM.savecomm_node(node)
        if not self.CM.isolate_node(member,allownodes1):
                return self.failure("Could not isolate the nodes")
        for member in partition2:
            if float(self.CM.Env["XmitLoss"])!=0 or float(self.CM.Env["RecvLoss"])!=0 :
                self.CM.savecomm_node(node)
            if not self.CM.isolate_node(member,allownodes2):
                return self.failure("Could not isolate the nodes")
        
        if not watchdead.lookforall():
            for member in self.CM.Env["nodes"]:
                self.CM.unisolate_node(member)
            self.CM.log("Patterns not found: " + repr(watchdead.unmatched))
            return self.failure("Didn't find the log 'dead' message")
        
        dcnum=0
        while dcnum < 2:
            dcnum = 0
            for member in self.CM.Env["nodes"]:
                if self.CM.is_node_dc(member):
                    dcnum += 1
            time.sleep(1)  
                    
        '''
        Unisolate the node, look for the return partition message
        and check whether they restart
        '''
        watchpartitionpats = [self.CM["Pat:DC_IDLE"]]
        partitionpat = self.CM["Pat:Return_partition"]
        for member in self.CM.Env["nodes"]:
            thispat = (partitionpat % member)
            watchpartitionpats.append(thispat)
        
        watchpartition = CTS.LogWatcher(self.CM["LogFileName"], watchpartitionpats\
        ,               timeout=self.CM["DeadTime"]+60)
        watchpartition.setwatch()
        
        for member in self.CM.Env["nodes"]:
            if float(self.CM.Env["XmitLoss"])!=0 or float(self.CM.Env["RecvLoss"])!=0 :
                self.CM.restorecomm_node(node)
            self.CM.unisolate_node(member)

        if not watchpartition.lookforall():
            self.CM.log("Patterns not found: " + repr(watchpartition.unmatched))
            return self.failure("Didn't find return from partition messages")
        
        return self.success()

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2":
            return 1
        return 0

    def errorstoignore(self):
        '''Return list of errors which are 'normal' and should be ignored'''
        return [ "ERROR:.*Both machines own.*resources"
        ,        "ERROR:.*lost a lot of packets!"
        ,        "ERROR: Cannot rexmit pkt .*: seqno too low"
        ,        "ERROR: Irretrievably lost packet: node"
        ]

#AllTestClasses.append(Split_brainTest2)

####################################################################
class MemoryTest(CTSTest):
####################################################################
    '''Check to see if anyone is leaking memory'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="Memory"
#        self.test = ElectionMemoryTest(cm)
        self.test = ResourceRecover(cm)
        self.startall = SimulStartLite(cm)
        self.before = {}
        self.after = {}

    def __call__(self, node):
        ps_command='''ps -eo ucomm,pid,pmem,tsiz,dsiz,rss,vsize | grep -e ccm -e ha_logd -e cib -e crmd -e lrmd -e tengine -e pengine'''

        memory_error = [ 
            "", "", "", 
            "Code", 
            "Data", 
            "Resident", 
            "Total" 
            ]
        
        ret = self.startall(None)
        if not ret:
            return self.failure("Test setup failed")

        time.sleep(10)  

        for node in self.CM.Env["nodes"]:
            self.before[node] = {}
            rsh_pipe = self.CM.rsh.popen(node, ps_command)
            rsh_pipe.tochild.close()
            result = rsh_pipe.fromchild.readline()
            while result:
                tokens = result.split()
                self.before[node][tokens[1]] = result
                result = rsh_pipe.fromchild.readline()
            rsh_pipe.fromchild.close()
            self.lastrc = rsh_pipe.wait()

        # do something...
        if not self.test(node):
            return self.failure("Underlying test failed")

        time.sleep(10)  

        for node in self.CM.Env["nodes"]:
            self.after[node] = {}
            rsh_pipe = self.CM.rsh.popen(node, ps_command)
            rsh_pipe.tochild.close()
            result = rsh_pipe.fromchild.readline()
            while result:
                tokens = result.split()
                self.after[node][tokens[1]] = result
                result = rsh_pipe.fromchild.readline()
            rsh_pipe.fromchild.close()
            self.lastrc = rsh_pipe.wait()

        failed_nodes = []
        for node in self.CM.Env["nodes"]:
            failed = 0
            for process in self.before[node]:
                messages = []
                before_line = self.before[node][process]
                after_line = self.after[node][process]

                if not after_line:
                    self.CM.log("%s %s[%s] exited during the test"
                              %(node, before_tokens[0], before_tokens[1]))
                    continue

                before_tokens = before_line.split()
                after_tokens = after_line.split()
                
                # 3 : Code size
                # 4 : Data size
                # 5 : Resident size
                # 6 : Total size
                for index in [ 3, 4, 6 ]:
                    mem_before = int(before_tokens[index])
                    mem_after  = int(after_tokens[index])
                    mem_diff   = mem_after - mem_before
                    mem_allow  = mem_before * 0.01
                    
                    # for now...
                    mem_allow  = 0

                    if mem_diff > mem_allow:
                        failed = 1
                        messages.append("%s size grew by %dkB (%dkB)"
                                        %(memory_error[index], mem_diff, mem_after))
                    elif mem_diff < 0:
                        messages.append("%s size shrank by %dkB (%dkB)"
                                        %(memory_error[index], mem_diff, mem_after))

                if len(messages) > 0:
                    self.CM.log("Process %s[%s] on %s: %s"
                                %(before_tokens[0], before_tokens[1], node,
                                  repr(messages)))
                    self.CM.debug("%s Before: %s[%s] (%s%%):\tcode=%skB, data=%skB, resident=%skB, total=%skB"
                                  %(node, before_tokens[0], before_tokens[1],
                                    before_tokens[2], before_tokens[3], 
                                    before_tokens[4], before_tokens[5],
                                    before_tokens[6]))
                    self.CM.debug("%s After:  %s[%s] (%s%%):\tcode=%skB, data=%skB, resident=%skB, total=%skB"
                                  %(node, after_tokens[0], after_tokens[1],
                                    after_tokens[2], after_tokens[3],
                                    after_tokens[4], after_tokens[5],
                                    after_tokens[6]))
                    
            if failed == 1:
                failed_nodes.append(node)

        if len(failed_nodes) > 0:
            return self.failure("Memory leaked on: " + repr(failed_nodes))

        return self.success()

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return [ """ERROR: .* LRM operation.*monitor on .*: not running""",
                 """pengine:.*Handling failed """]

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2":
            return 1
        return 0

#AllTestClasses.append(MemoryTest)

####################################################################
class ElectionMemoryTest(CTSTest):
####################################################################
    '''Check to see if anyone is leaking memory'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="Election"

    def __call__(self, node):
        self.rsh.readaline(node, self.CM["ElectionCmd"]%node)

        if self.CM.cluster_stable():
            return self.success()
        
        return self.failure("Cluster not stable")

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        '''Never applicable, only for use by the memory test'''
        return 0

AllTestClasses.append(ElectionMemoryTest)


####################################################################
class SpecialTest1(CTSTest):
####################################################################
    '''Set up a custom test to cause quorum failure issues for Andrew'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="SpecialTest1"
        self.startall = SimulStartLite(cm)
        self.restart1 = RestartTest(cm)
        self.stopall = SimulStopLite(cm)

    def __call__(self, node):
        '''Perform the 'SpecialTest1' test for Andrew. '''
        self.incr("calls")
        #        Shut down all the nodes...
        ret = self.stopall(None)
        if not ret:
            return ret
        #        Start the selected node
        ret = self.restart1(node)
        if not ret:
            return ret
        #        Start all remaining nodes
        ret = self.startall(None)
        return ret

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        return 1

AllTestClasses.append(SpecialTest1)
###################################################################
class NearQuorumPointTest(CTSTest):
###################################################################
    '''
    This test brings larger clusters near the quorum point (50%).
    In addition, it will test doing starts and stops at the same time.

    Here is how I think it should work:
    - loop over the nodes and decide randomly which will be up and which
      will be down  Use a 50% probability for each of up/down.
    - figure out what to do to get into that state from the current state
    - in parallel, bring up those going up  and bring those going down.
    '''
    
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="NearQuorumPoint"

    def __call__(self, dummy):
        '''Perform the 'NearQuorumPoint' test. '''
        self.incr("calls")
        startset = []
        stopset = []
       
        #decide what to do with each node
        for node in self.CM.Env["nodes"]:
            action = self.CM.Env.RandomGen.choice(["start","stop"])
            #action = self.CM.Env.RandomGen.choice(["start","stop","no change"])
            if action == "start" :
                startset.append(node)
            elif action == "stop" :
                stopset.append(node)
                
        self.CM.debug("start nodes:" + repr(startset))
        self.CM.debug("stop nodes:" + repr(stopset))

        #add search patterns
        watchpats = [ ]
        for node in stopset:
            if self.CM.ShouldBeStatus[node] == self.CM["up"]:
                watchpats.append(self.CM["Pat:We_stopped"] % node)
                
        for node in startset:
            if self.CM.ShouldBeStatus[node] == self.CM["down"]:
                watchpats.append(self.CM["Pat:They_started"] % node)
                
        if len(watchpats) == 0:
            return self.skipped()

        if len(startset) != 0:
            watchpats.append(self.CM["Pat:DC_IDLE"])

        watch = CTS.LogWatcher(self.CM["LogFileName"], watchpats
        ,     timeout=self.CM["DeadTime"]+10)
        
        watch.setwatch()
        
        #begin actions
        for node in stopset:
            if self.CM.ShouldBeStatus[node] == self.CM["up"]:
                self.CM.StopaCMnoBlock(node)
                
        for node in startset:
            if self.CM.ShouldBeStatus[node] == self.CM["down"]:
                self.CM.StartaCMnoBlock(node)
        
        #get the result        
        if watch.lookforall():
            self.CM.cluster_stable()
            return self.success()

        self.CM.log("Warn: Patterns not found: " + repr(watch.unmatched))
        
        #get the "bad" nodes
        upnodes = []        
        for node in stopset:
            if self.CM.StataCM(node) == 1:
                upnodes.append(node)
        
        downnodes = []
        for node in startset:
            if self.CM.StataCM(node) == 0:
                downnodes.append(node)

        if upnodes == [] and downnodes == []:
            self.CM.cluster_stable()
            return self.success()

        if len(upnodes) > 0:
            self.CM.log("Warn: Unstoppable nodes: " + repr(upnodes))
        
        if len(downnodes) > 0:
            self.CM.log("Warn: Unstartable nodes: " + repr(downnodes))
        
        return self.failure()

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2":
            return 1
        return 0

AllTestClasses.append(NearQuorumPointTest)

###################################################################
class BSC_AddResource(CTSTest):
###################################################################
    '''Add a resource to the cluster'''
    def __init__(self, cm):
        CTSTest.__init__(self, cm)
        self.name="AddResource"
        self.resource_offset = 0
        self.cib_cmd="""/usr/sbin/cibadmin -C -o %s -X '%s' """

    def __call__(self, node):
        self.resource_offset =         self.resource_offset  + 1

        r_id = "bsc-rsc-%s-%d" % (node, self.resource_offset)
        start_pat = "crmd.*%s_start_0.*complete"

        patterns = []
        patterns.append(start_pat % r_id)

        watch = CTS.LogWatcher(
            self.CM["LogFileName"], patterns, self.CM["DeadTime"])
        watch.setwatch()

        fields = string.split(self.CM.Env["IPBase"], '.')
        fields[3] = str(int(fields[3])+1)
        ip = string.join(fields, '.')
        self.CM.Env["IPBase"] = ip

        if not self.make_ip_resource(node, r_id, "ocf", "IPaddr", ip):
            return self.failure("Make resource %s failed" % r_id)

        failed = 0
        watch_result = watch.lookforall()
        if watch.unmatched:
            for regex in watch.unmatched:
                self.CM.log ("Warn: Pattern not found: %s" % (regex))
                failed = 1

        if failed:
            return self.failure("Resource pattern(s) not found")

        if not self.CM.cluster_stable(self.CM["DeadTime"]):
            return self.failure("Unstable cluster")

        return self.success()

    def make_ip_resource(self, node, id, rclass, type, ip):
        self.CM.log("Creating %s::%s:%s (%s) on %s" % (rclass,type,id,ip,node))
        rsc_xml="""
<primitive id="%s" class="%s" type="%s"  provider="heartbeat">
    <instance_attributes id="%s"><attributes>
        <nvpair id="%s" name="ip" value="%s"/>
    </attributes></instance_attributes>
</primitive>""" % (id, rclass, type, id, id, ip)

        node_constraint="""
      <rsc_location id="run_%s" rsc="%s">
        <rule id="pref_run_%s" score="100">
          <expression id="%s_loc_expr" attribute="#uname" operation="eq" value="%s"/>
        </rule>
      </rsc_location>""" % (id, id, id, id, node)

        rc = 0
        (rc, lines) = self.CM.rsh.remote_py(node, "os", "system", self.cib_cmd % ("constraints", node_constraint))
        if rc != 0:
            self.CM.log("Constraint creation failed: %d" % rc)
            return None

        (rc, lines) = self.CM.rsh.remote_py(node, "os", "system", self.cib_cmd % ("resources", rsc_xml))
        if rc != 0:
            self.CM.log("Resource creation failed: %d" % rc)
            return None

        return 1

    def is_applicable(self):
        if self.CM["Name"] == "linux-ha-v2" and self.CM.Env["DoBSC"]:
            return 1
        return None

def TestList(cm):
    result = []
    for testclass in AllTestClasses:
        bound_test = testclass(cm)
        if bound_test.is_applicable():
            result.append(bound_test)
    return result

         

class SimulStopLite(CTSTest):
###################################################################
    '''Stop any active nodes ~ simultaneously'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="SimulStopLite"

    def __call__(self, dummy):
        '''Perform the 'SimulStopLite' setup work. '''
        self.incr("calls")

        self.CM.debug("Setup: " + self.name)

        #     We ignore the "node" parameter...
        watchpats = [ ]

        for node in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[node] == self.CM["up"]:
                self.incr("WasStarted")
                watchpats.append(self.CM["Pat:All_stopped"] % node)
                if self.CM.Env["use_logd"]:
                    watchpats.append(self.CM["Pat:Logd_stopped"] % node)

        if len(watchpats) == 0:
            self.CM.clear_all_caches()
            return self.skipped()

        #     Stop all the nodes - at about the same time...
        watch = CTS.LogWatcher(self.CM["LogFileName"], watchpats
        ,     timeout=self.CM["DeadTime"]+10)

        watch.setwatch()
        self.starttime=time.time()
        for node in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[node] == self.CM["up"]:
                self.CM.StopaCMnoBlock(node)
        if watch.lookforall():
            self.CM.clear_all_caches()
            return self.success()

        did_fail=0
        up_nodes = []
        for node in self.CM.Env["nodes"]:
            if self.CM.StataCM(node) == 1:
                did_fail=1
                up_nodes.append(node)

        if did_fail:
            return self.failure("Active nodes exist: " + repr(up_nodes))

        self.CM.log("Warn: All nodes stopped but CTS didnt detect: " 
                    + repr(watch.unmatched))

        self.CM.clear_all_caches()
        return self.failure("Missing log message: "+repr(watch.unmatched))

    def is_applicable(self):
        '''SimulStopLite is a setup test and never applicable'''
        return 0

###################################################################
class SimulStartLite(CTSTest):
###################################################################
    '''Start any stopped nodes ~ simultaneously'''
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="SimulStartLite"
        
    def __call__(self, dummy):
        '''Perform the 'SimulStartList' setup work. '''
        self.incr("calls")
        self.CM.debug("Setup: " + self.name)

        #        We ignore the "node" parameter...
        watchpats = [ ]

        for node in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[node] == self.CM["down"]:
                self.incr("WasStopped")
                watchpats.append(self.CM["Pat:They_started"] % node)
        
        if len(watchpats) == 0:
            return self.skipped()
        
        #        Start all the nodes - at about the same time...
        watch = CTS.LogWatcher(self.CM["LogFileName"], watchpats
        ,        timeout=self.CM["DeadTime"]+10)

        watch.setwatch()

        self.starttime=time.time()
        for node in self.CM.Env["nodes"]:
            if self.CM.ShouldBeStatus[node] == self.CM["down"]:
                self.CM.StartaCMnoBlock(node)
        if watch.lookforall():
            for attempt in (1, 2, 3, 4, 5):
                if self.CM.cluster_stable():
                    return self.success()
            return self.failure("Cluster did not stabilize") 
                
        did_fail=0
        unstable = []
        for node in self.CM.Env["nodes"]:
            if self.CM.StataCM(node) == 0:
                did_fail=1
                unstable.append(node)
                
        if did_fail:
            return self.failure("Unstarted nodes exist: " + repr(unstable))

        unstable = []
        for node in self.CM.Env["nodes"]:
            if not self.CM.node_stable(node):
                did_fail=1
                unstable.append(node)

        if did_fail:
            return self.failure("Unstable cluster nodes exist: " 
                                + repr(unstable))

        self.CM.log("ERROR: All nodes started but CTS didnt detect: " 
                    + repr(watch.unmatched))
        return self.failure() 


    def is_applicable(self):
        '''SimulStartLite is a setup test and never applicable'''
        return 0

###################################################################
class LoggingTest(CTSTest):
###################################################################
    def __init__(self, cm):
        CTSTest.__init__(self,cm)
        self.name="Logging"

    def __call__(self, dummy):
        '''Perform the 'Logging' test. '''
        self.incr("calls")
        
        # Make sure logging is working and we have enough disk space...
        if not self.CM.TestLogging():
            sys.exit(1)
        if not self.CM.CheckDf():
            sys.exit(1)

    def is_applicable(self):
        '''ResourceRecover is applicable only when there are resources running
         on our cluster and environment is linux-ha-v2'''
        return self.CM.Env["DoBSC"]

    def errorstoignore(self):
        '''Return list of errors which should be ignored'''
        return []

#AllTestClasses.append(LoggingTest)
