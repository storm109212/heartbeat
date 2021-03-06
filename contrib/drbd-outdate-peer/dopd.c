/* drbd outdate peer daemon
 * Copyright (C) 2006 LINBIT <http://www.linbit.com/>
 * Written by Rasto Levrinc <rasto@linbit.com>
 *
 * based on ipfail.c and attrd.c
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <lha_internal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <stdarg.h>
#include <libgen.h>
#include <pthread.h> /* linux specific; well, so is dopd. */
#include <heartbeat.h>
#include <ha_msg.h>
#include <hb_api.h>
#include <clplumbing/cl_signal.h>
#include <clplumbing/GSource.h>
#include <clplumbing/Gmain_timeout.h>
#include <clplumbing/coredumps.h>
#include <dopd.h>
#include <clplumbing/cl_misc.h>

const char *node_name;	   /* The node we are connected to	      */
int quitnow = 0;	   /* Allows a signal to break us out of loop */
GMainLoop *mainloop;	   /* Reference to the mainloop for events    */
ll_cluster_t *dopd_cluster_conn;

GHashTable *connections = NULL;
pthread_mutex_t conn_mutex = PTHREAD_MUTEX_INITIALIZER;

/* only one client can be connected at a time */

typedef struct dopd_client_s
{
	char *id;
	char *drbd_res;

	IPC_Channel *channel;
	GCHSource   *source;
} dopd_client_t;

/* send_message_to_the_peer()
 * send message with drbd resource to other node.
 */
static gboolean
send_message_to_the_peer(const char *drbd_peer, const char *drbd_resource)
{
	HA_Message *msg = NULL;

	cl_log(LOG_INFO, "sending start_outdate message to the other node %s -> %s",
		  node_name, drbd_peer);

	msg = ha_msg_new(3);
	ha_msg_add(msg, F_TYPE, "start_outdate");
	ha_msg_add(msg, F_ORIG, node_name);
	ha_msg_add(msg, F_DOPD_RES, drbd_resource);

	cl_log(LOG_DEBUG, "sending [start_outdate res: %s] to node: %s",
		  drbd_resource, drbd_peer);
	dopd_cluster_conn->llc_ops->sendnodemsg(dopd_cluster_conn, msg, drbd_peer);
	ha_msg_del(msg);

	return TRUE;
}

static void
send_to_client(const dopd_client_t *client, const char *rc_string)
{
	IPC_Channel *channel = client->channel;
	HA_Message *msg_out;

	msg_out = ha_msg_new(3);
	ha_msg_add(msg_out, F_TYPE, "outdater_rc");
	ha_msg_add(msg_out, F_ORIG, node_name);
	ha_msg_add(msg_out, F_DOPD_VALUE, rc_string);

	if (msg2ipcchan(msg_out, channel) != HA_OK) {
		cl_log(LOG_ERR, "Could not send message to the client");
	}
}

/* msg_start_outdate()
 * got start_outdate message with resource from other node. Execute drbd
 * outdate command, convert return code and send message to other node
 * with return code.
 *
 * Conversion of return codes of "drbdadm outdate <resourcename>":
 *     0 => 4 (was successfully outdated)
 *     5 => 3 (is inconsistent, anyways)
 *    17 => 6 (is primary, cannot be outdated)
 * other => 20 (which is "officially undefined",
 *              unspecified error, could not be outdated)
 *
 * since we do not stonith,
 * we cannot return "7" peer got stonithed [ node fencing ].
 * and since we have obviously been reached,
 * we must not return "5" (down/unreachable).
 */
void
msg_start_outdate(struct ha_msg *msg, void *private)
{
	ll_cluster_t *hb = (ll_cluster_t *)private;
	int rc = 20;
	int command_ret;

	char rc_string[4];
	HA_Message *msg2 = NULL;
	const char *drbd_resource = ha_msg_value(msg, F_DOPD_RES);
	char *command = NULL;

	/* execute outdate command */
	command = cl_malloc(strlen(OUTDATE_COMMAND) + 1 + strlen(drbd_resource) + 1);
	strcpy(command, OUTDATE_COMMAND);
	strcat(command, " ");
	strcat(command, drbd_resource);
	cl_log(LOG_DEBUG, "msg_start_outdate: command: %s", command);
	command_ret = system(command);

	if (WIFEXITED(command_ret)) {
		/* normal exit */
		command_ret = WEXITSTATUS(command_ret);

		/* convert return code */
		if (command_ret == 0)
			rc = 4;
		else if (command_ret == 5)
			rc = 3;
		else if (command_ret == 17)
			rc = 6;
		else
			cl_log(LOG_INFO, "unknown exit code from %s: %i",
					command, command_ret);
	} else {
		/* something went wrong */
                if (WIFSIGNALED(command_ret)) {
			cl_log(LOG_INFO, "killed by signal %i: %s",
					WTERMSIG(command_ret), command);
		} else {
			cl_log(LOG_INFO, "strange status code from %s: 0x%x",
					command, command_ret);
		}
	}

	cl_free(command);

	cl_log(LOG_DEBUG, "msg_start_outdate: %s, command rc: %i, rc: %i",
			 ha_msg_value(msg, F_ORIG), command_ret, rc);
	sprintf(rc_string, "%i", rc);

	cl_log(LOG_INFO, "sending return code: %s, %s -> %s\n",
			rc_string, node_name, ha_msg_value(msg, F_ORIG));
	/* send return code to oder node */
	msg2 = ha_msg_new(4);
	ha_msg_add(msg2, F_TYPE, "outdate_rc");
	ha_msg_add(msg2, F_DOPD_VALUE, rc_string);
	ha_msg_add(msg2, F_DOPD_RES, drbd_resource);
	ha_msg_add(msg2, F_ORIG, node_name);

	hb->llc_ops->sendnodemsg(hb, msg2, ha_msg_value(msg, F_ORIG));
	ha_msg_del(msg2);
}

/* msg_outdate_rc()
 * got outdate_rc message with return code from other node. Send the
 * return code to the outdater client.
 */
void
msg_outdate_rc(struct ha_msg *msg_in, void *private)
{
	const char *rc_string = ha_msg_value(msg_in, F_DOPD_VALUE);
	const char *rc_res = ha_msg_value(msg_in, F_DOPD_RES);

	dopd_client_t *client = g_hash_table_lookup(connections, rc_res);

	cl_log(LOG_DEBUG, "msg_outdate_rc: %s %s", rc_res, rc_string);
	if (client == NULL)
		return;
	send_to_client(client, rc_string);
}

/* check_drbd_peer()
 * walk the nodes and return TRUE if peer is not this node and it exists.
 */
gboolean
check_drbd_peer(const char *drbd_peer)
{
	const char *node;
	gboolean found = FALSE;
	if (!strcmp(drbd_peer, node_name)) {
		cl_log(LOG_WARNING, "drbd peer node %s is me!\n", drbd_peer);
		return FALSE;
	}

	cl_log(LOG_DEBUG, "Starting node walk");
	if (dopd_cluster_conn->llc_ops->init_nodewalk(dopd_cluster_conn) != HA_OK) {
		cl_log(LOG_WARNING, "Cannot start node walk");
		cl_log(LOG_WARNING, "REASON: %s",
		       dopd_cluster_conn->llc_ops->errmsg(dopd_cluster_conn));
		return FALSE;
	}
	while((node = dopd_cluster_conn->llc_ops->nextnode(dopd_cluster_conn)) != NULL) {
		const char *status = dopd_cluster_conn->llc_ops->node_status(dopd_cluster_conn, node);
		if (!strcmp(status, "dead")) {
			cl_log(LOG_WARNING, "Cluster node: %s: status: %s",
			       node, status);
			return FALSE;
		}

		/* Look for the peer */
		if (!strcmp("normal", dopd_cluster_conn->llc_ops->node_type(dopd_cluster_conn, node))
			&& !strcmp(node, drbd_peer)) {
			cl_log(LOG_DEBUG, "node %s found\n", node);
			found = TRUE;
			break;
		}
	}
	if (dopd_cluster_conn->llc_ops->end_nodewalk(dopd_cluster_conn) != HA_OK) {
		cl_log(LOG_INFO, "Cannot end node walk");
		cl_log(LOG_INFO, "REASON: %s", dopd_cluster_conn->llc_ops->errmsg(dopd_cluster_conn));
	}

	if (found == FALSE)
		cl_log(LOG_WARNING, "drbd peer %s was not found\n", drbd_peer);
	return found;
}

/* outdater_callback()
 * got message from outdater client with drbd resource, it will be sent
 * to the other node.
 */
static gboolean
outdater_callback(IPC_Channel *client, gpointer user_data)
{
	int lpc = 0;
	HA_Message *msg = NULL;
	const char *drbd_peer = NULL;
	const char *drbd_resource = NULL;
	dopd_client_t *curr_client = (dopd_client_t*)user_data;
	gboolean stay_connected = TRUE;

	cl_log(LOG_DEBUG, "invoked: %s", curr_client->id);

	while (IPC_ISRCONN(client)) {
		if(client->ops->is_message_pending(client) == 0) {
			break;
		}

		msg = msgfromIPC_noauth(client);
		if (msg == NULL) {
			cl_log(LOG_DEBUG, "%s: no message this time",
				  curr_client->id);
			continue;
		}

		lpc++;

		cl_log(LOG_DEBUG, "Processing msg from %s", curr_client->id);
		cl_log(LOG_DEBUG, "Got message from (%s). (peer: %s, res :%s)",
				ha_msg_value(msg, F_ORIG),
				ha_msg_value(msg, F_OUTDATER_PEER),
				ha_msg_value(msg, F_OUTDATER_RES));

		drbd_resource = ha_msg_value(msg, F_OUTDATER_RES);
		drbd_peer = ha_msg_value(msg, F_OUTDATER_PEER);
		if (check_drbd_peer(drbd_peer)) {
			dopd_client_t *entry;
			pthread_mutex_lock(&conn_mutex);
			entry = g_hash_table_lookup(connections,
						     drbd_resource);
			if (entry == NULL) {
				curr_client->drbd_res = strdup(drbd_resource);
				if (entry  == NULL)
					g_hash_table_insert(connections,
							    curr_client->drbd_res,
							    curr_client);
				pthread_mutex_unlock(&conn_mutex);
				send_message_to_the_peer(drbd_peer, drbd_resource);
			} else if (entry != curr_client) {
				pthread_mutex_unlock(&conn_mutex);
				cl_log(LOG_DEBUG, "one client with %s already "
				       "connected", drbd_resource);
				send_to_client(curr_client, "21");
			} else
				pthread_mutex_unlock(&conn_mutex);
		} else {
			/* wrong peer was specified,
			   send return code 20 to the client */
			send_to_client(curr_client, "20");
		}

		ha_msg_del(msg);
		msg = NULL;

		if(client->ch_status != IPC_CONNECT) {
			break;
		}
	}
	cl_log(LOG_DEBUG, "Processed %d messages", lpc);
	if (client->ch_status != IPC_CONNECT)
		stay_connected = FALSE;
	return stay_connected;
}

/* outdater_ipc_connection_destroy()
 * clean client struct
 */
static void
outdater_ipc_connection_destroy(gpointer user_data)
{
	dopd_client_t *client = (dopd_client_t*)user_data;

	if (client == NULL)
		return;
	cl_log(LOG_DEBUG, "destroying connection: %s\n", client->drbd_res);
	if (client->source != NULL) {
		if (client->drbd_res != NULL) {
			dopd_client_t *entry = g_hash_table_lookup(connections,
								   client->drbd_res);
			if (entry == client)
				g_hash_table_remove(connections, 
						    (gpointer)client->drbd_res);
		}
		cl_log(LOG_DEBUG, "Deleting %s (%p) from mainloop",
				client->id, client->source);
		G_main_del_IPC_Channel(client->source);
		client->source = NULL;
		//cl_free(client->drbd_res);
	}
	cl_free(client->id);
	cl_free(client);
	return;
}

/* outdater_client_connect()
 * outdater is connected set outdater_callback.
 */
static gboolean
outdater_client_connect(IPC_Channel *channel, gpointer user_data)
{
	dopd_client_t *new_client = cl_malloc(sizeof(dopd_client_t));
	cl_log(LOG_DEBUG, "Connecting channel");
	if(channel == NULL) {
		cl_log(LOG_ERR, "Channel was NULL");
		return FALSE;

	} else if(channel->ch_status != IPC_CONNECT) {
		cl_log(LOG_ERR, "Channel was disconnected");
		return FALSE;
	}

	memset(new_client, 0, sizeof(dopd_client_t));

	new_client->channel = channel;
	new_client->id = cl_malloc(10);
	strcpy(new_client->id, "outdater");

	new_client->source = G_main_add_IPC_Channel(
		G_PRIORITY_DEFAULT, channel, FALSE, outdater_callback,
		new_client, outdater_ipc_connection_destroy);

	cl_log(LOG_DEBUG, "Client %s (%p) connected",
			  new_client->id,
			  new_client->source);

	return TRUE;
}

static void
outdater_client_destroy(gpointer user_data)
{
	cl_log(LOG_INFO, "ipc server destroy");
}

/* set_callbacks()
 * set callbacks for communication between two nodes
 */
void
set_callbacks(ll_cluster_t *hb)
{
	/* Add each of the callbacks we use with the API */
	if (hb->llc_ops->set_msg_callback(hb, "start_outdate",
					  msg_start_outdate, hb) != HA_OK) {
		cl_log(LOG_ERR, "Cannot set msg_start_outdate callback");
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		exit(2);
	}

	if (hb->llc_ops->set_msg_callback(hb, "outdate_rc",
					  msg_outdate_rc, hb) != HA_OK) {
		cl_log(LOG_ERR, "Cannot set msg_outdate_rc callback");
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		exit(2);
	}
}

void
set_signals(ll_cluster_t *hb)
{
	/* Setup the various signals */

	CL_SIGINTERRUPT(SIGINT, 1);
	CL_SIGNAL(SIGINT, gotsig);
	CL_SIGINTERRUPT(SIGTERM, 1);
	CL_SIGNAL(SIGTERM, gotsig);

	cl_log(LOG_DEBUG, "Setting message signal");
	if (hb->llc_ops->setmsgsignal(hb, 0) != HA_OK) {
		cl_log(LOG_ERR, "Cannot set message signal");
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		exit(13);
	}
}

void
gotsig(int nsig)
{
	(void)nsig;
	quitnow = 1;
}

/* Used to handle the API in the gmainloop */
gboolean
dopd_dispatch(IPC_Channel* ipc, gpointer user_data)
{
	struct ha_msg *reply;
	ll_cluster_t *hb = user_data;

	reply = hb->llc_ops->readmsg(hb, 0);

	if (reply != NULL) {
		ha_msg_del(reply); reply=NULL;
		return TRUE;
	}
	return TRUE;
}

void
dopd_dispatch_destroy(gpointer user_data)
{
	return;
}

gboolean
dopd_timeout_dispatch(gpointer user_data)
{
	ll_cluster_t *hb = user_data;

	if (quitnow) {
		g_main_quit(mainloop);
		return FALSE;
	}
	if (hb->llc_ops->msgready(hb)) {
		return dopd_dispatch(NULL, user_data);
	}
	return TRUE;
}

/* Sign in to the API */
void
open_api(ll_cluster_t *hb)
{
	cl_log(LOG_DEBUG, "Signing in with heartbeat");
	if (hb->llc_ops->signon(hb, "dopd")!= HA_OK) {
		cl_log(LOG_ERR, "Cannot sign on with heartbeat");
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		exit(1);
	}
}

/* Log off of the API and clean up */
void
close_api(ll_cluster_t *hb)
{
	if (hb->llc_ops->signoff(hb, FALSE) != HA_OK) {
		cl_log(LOG_ERR, "Cannot sign off from heartbeat.");
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		exit(14);
	}
	if (hb->llc_ops->delete(hb) != HA_OK) {
		cl_log(LOG_ERR, "REASON: %s", hb->llc_ops->errmsg(hb));
		cl_log(LOG_ERR, "Cannot delete API object.");
		exit(15);
	}
}

static IPC_WaitConnection *
dopd_channel_init(char daemonsocket[])
{
	IPC_WaitConnection *wait_ch;
	mode_t mask;
	char path[] = IPC_PATH_ATTR;
	GHashTable * attrs;

	attrs = g_hash_table_new(g_str_hash,g_str_equal);
	g_hash_table_insert(attrs, path, daemonsocket);

	mask = umask(0);
	wait_ch = ipc_wait_conn_constructor(IPC_ANYTYPE, attrs);
	if (wait_ch == NULL) {
		cl_perror("Can't create wait channel of type %s",
			  IPC_ANYTYPE);
		exit(1);
	}
	mask = umask(mask);

	g_hash_table_destroy(attrs);

	return wait_ch;
}

int
main(int argc, char **argv)
{
	unsigned fmask;
	char pid[10];
	char *bname, *parameter;
	IPC_Channel *apiIPC;

	char commpath[1024];
	IPC_WaitConnection *wait_ch;

	/* Get the name of the binary for logging purposes */
	bname = cl_strdup(argv[0]);

	cl_log_set_entity(bname);
	cl_log_set_facility(HA_LOG_FACILITY);
	cl_log_set_logd_channel_source(NULL, NULL);
	cl_inherit_logging_environment(500);
	cl_set_corerootdir(HA_COREDIR);
	cl_cdtocoredir();

	dopd_cluster_conn = ll_cluster_new("heartbeat");

	memset(pid, 0, sizeof(pid));
	snprintf(pid, sizeof(pid), "%ld", (long)getpid());
	cl_log(LOG_DEBUG, "PID=%s", pid);

	open_api(dopd_cluster_conn);

	/* Obtain our local node name */
	node_name = dopd_cluster_conn->llc_ops->get_mynodeid(dopd_cluster_conn);
	if (node_name == NULL) {
		cl_log(LOG_ERR, "Cannot get my nodeid");
		cl_log(LOG_ERR, "REASON: %s", dopd_cluster_conn->llc_ops->errmsg(dopd_cluster_conn));
		exit(19);
	}
	cl_log(LOG_DEBUG, "[We are %s]", node_name);

	/* See if we should drop cores somewhere odd... */
	parameter = dopd_cluster_conn->llc_ops->get_parameter(dopd_cluster_conn, KEY_COREROOTDIR);
	if (parameter) {
		cl_set_corerootdir(parameter);
		cl_cdtocoredir();
	}
	cl_cdtocoredir();


	set_callbacks(dopd_cluster_conn);

	fmask = LLC_FILTER_DEFAULT;

	cl_log(LOG_DEBUG, "Setting message filter mode");
	if (dopd_cluster_conn->llc_ops->setfmode(dopd_cluster_conn, fmask) != HA_OK) {
		cl_log(LOG_ERR, "Cannot set filter mode");
		cl_log(LOG_ERR, "REASON: %s", dopd_cluster_conn->llc_ops->errmsg(dopd_cluster_conn));
		exit(8);
	}

	connections = g_hash_table_new_full(
	              g_str_hash, g_str_equal, NULL, NULL);

	set_signals(dopd_cluster_conn);

	cl_log(LOG_DEBUG, "Waiting for messages...");
	errno = 0;

	mainloop = g_main_new(TRUE);

	apiIPC = dopd_cluster_conn->llc_ops->ipcchan(dopd_cluster_conn);

	/* Watch the API IPC for input */
	G_main_add_IPC_Channel(G_PRIORITY_HIGH, apiIPC, FALSE,
			       dopd_dispatch, (gpointer)dopd_cluster_conn,
			       dopd_dispatch_destroy);

	Gmain_timeout_add_full(G_PRIORITY_DEFAULT, 1000,
				dopd_timeout_dispatch, (gpointer)dopd_cluster_conn,
				dopd_dispatch_destroy);

	memset(commpath, 0, 1024);
	sprintf(commpath, HA_VARRUNDIR"/heartbeat/crm/%s", T_OUTDATER);

	wait_ch = dopd_channel_init(commpath);
	if (wait_ch == NULL) {
		cl_log(LOG_ERR, "Could not start IPC server");
	} else {
	    G_main_add_IPC_WaitConnection(
		G_PRIORITY_LOW, wait_ch, NULL, FALSE,
		outdater_client_connect, cl_strdup(T_OUTDATER),
		outdater_client_destroy);
	}

	g_main_run(mainloop);
	g_main_destroy(mainloop);

	g_hash_table_destroy(connections);

	if (!quitnow && errno != EAGAIN && errno != EINTR) {
		cl_log(LOG_ERR, "read_hb_msg returned NULL");
		cl_log(LOG_ERR, "REASON: %s", dopd_cluster_conn->llc_ops->errmsg(dopd_cluster_conn));
	}

	close_api(dopd_cluster_conn);

	return 0;
}
