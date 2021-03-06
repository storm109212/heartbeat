/* 
 * Copyright (C) 2004 Andrew Beekhof <andrew@beekhof.net>
 * 
 * This program is free software; you can redistribute it and/or
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

#include <sys/param.h>
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

#include <string.h>
#include <stdlib.h>

#include <errno.h>
#include <fcntl.h>

#include <heartbeat.h>
#include <crm/crm.h>

#include <cibio.h>
#include <crm/cib.h>
#include <crm/common/util.h>
#include <crm/msg_xml.h>
#include <crm/common/xml.h>
#include <crm/common/util.h>
#include <clplumbing/cl_misc.h>
#include <clplumbing/lsb_exitcodes.h>

#include <cibprimatives.h>

int archive_file(const char *oldname, const char *newname, const char *ext, gboolean preserve);

const char * local_resource_path[] =
{
	XML_CIB_TAG_STATUS,
};

const char * resource_path[] =
{
	XML_CIB_TAG_RESOURCES,
};

const char * node_path[] =
{
	XML_CIB_TAG_NODES,
};

const char * constraint_path[] =
{
	XML_CIB_TAG_CONSTRAINTS,
};

gboolean initialized = FALSE;
crm_data_t *the_cib = NULL;
crm_data_t *node_search = NULL;
crm_data_t *resource_search = NULL;
crm_data_t *constraint_search = NULL;
crm_data_t *status_search = NULL;

extern gboolean cib_writes_enabled;
extern char *ccm_transition_id;
extern gboolean cib_have_quorum;
extern GHashTable *peer_hash;
extern GHashTable *ccm_membership;
extern GTRIGSource *cib_writer;
extern enum cib_errors cib_status;

int set_connected_peers(crm_data_t *xml_obj);
void GHFunc_count_peers(gpointer key, gpointer value, gpointer user_data);
int write_cib_contents(gpointer p);
extern void cib_cleanup(void);


static gboolean
validate_cib_digest(crm_data_t *local_cib, const char *sigfile)
{
	int s_res = -1;
	struct stat buf;
	char *digest = NULL;
	char *expected = NULL;
	gboolean passed = FALSE;
	FILE *expected_strm = NULL;
	int start = 0, length = 0, read_len = 0;
	
	CRM_ASSERT(sigfile != NULL);
	s_res = stat(sigfile, &buf);
	
	if (s_res != 0) {
		crm_warn("No on-disk digest present");
		return TRUE;
	}

	if(local_cib != NULL) {
	    digest = calculate_xml_digest(local_cib, FALSE, FALSE);
	}
	
	expected_strm = fopen(sigfile, "r");
	if(expected_strm == NULL) {
		cl_perror("Could not open signature file %s for reading", sigfile);
		goto bail;
	}

	start  = ftell(expected_strm);
	fseek(expected_strm, 0L, SEEK_END);
	length = ftell(expected_strm);
	fseek(expected_strm, 0L, start);
	
	CRM_ASSERT(start == ftell(expected_strm));

	crm_debug_3("Reading %d bytes from file", length);
	crm_malloc0(expected, (length+1));
	read_len = fread(expected, 1, length, expected_strm);
	CRM_ASSERT(read_len == length);
	fclose(expected_strm);

  bail:
	if(expected == NULL) {
		crm_err("On-disk digest is empty");
		
	} else if(safe_str_eq(expected, digest)) {
		crm_debug_2("Digest comparision passed: %s", digest);
		passed = TRUE;

	} else {
		crm_err("Digest comparision failed: expected %s (%s), calculated %s",
			expected, sigfile, digest);
	}

 	crm_free(digest);
 	crm_free(expected);
	return passed;
}

static int
write_cib_digest(crm_data_t *local_cib, char *digest)
{
	int rc = 0;
	char *local_digest = NULL;
	FILE *digest_strm = fopen(CIB_FILENAME ".sig", "w");
	if(digest_strm == NULL) {
		cl_perror("Cannot open signature file "CIB_FILENAME ".sig for writing");
		return -1;
	}

	if(digest == NULL) {
		local_digest = calculate_xml_digest(local_cib, FALSE, FALSE);
		CRM_ASSERT(digest != NULL);
		digest = local_digest;
	}
	
	rc = fprintf(digest_strm, "%s", digest);
	if(rc < 0) {
		cl_perror("Cannot write to signature file "CIB_FILENAME ".sig");
	}

	CRM_ASSERT(digest_strm != NULL);
	if(fflush(digest_strm) != 0) {
	    cl_perror("fflush for %s failed:", digest);
	    rc = -1;
	}
	
	if(fsync(fileno(digest_strm)) < 0) {
	    cl_perror("fsync for %s failed:", digest);
	    rc = -1;
	}
	
	fclose(digest_strm);
	crm_free(local_digest);
	return rc;
}

static gboolean
validate_on_disk_cib(const char *filename, crm_data_t **on_disk_cib)
{
	int s_res = -1;
	struct stat buf;
	FILE *cib_file = NULL;
	gboolean passed = TRUE;
	crm_data_t *root = NULL;

	CRM_ASSERT(filename != NULL);
	
	s_res = stat(filename, &buf);
	if (s_res == 0) {
		char *sigfile = NULL;
		size_t		fnsize;
		cib_file = fopen(filename, "r");
		if(cib_file == NULL) {
			cl_perror("Couldn't open config file %s for reading", filename);
			return FALSE;
		}

		crm_debug_2("Reading cluster configuration from: %s", filename);
		root = file2xml(cib_file, FALSE);
		fclose(cib_file);
		
		fnsize =  strlen(filename) + 5;
		crm_malloc0(sigfile, fnsize);
		snprintf(sigfile, fnsize, "%s.sig", filename);
		if(validate_cib_digest(root, sigfile) == FALSE) {
			passed = FALSE;
		}
		crm_free(sigfile);
	}
	
	if(on_disk_cib != NULL) {
		*on_disk_cib = root;
	} else {
		free_xml(root);
	}
	
	return passed;
}

static int
cib_unlink(const char *file)
{
    int rc = unlink(file);
    if (rc < 0) {
	cl_perror("Could not unlink %s - Disabling disk writes and continuing", file);
	cib_writes_enabled = FALSE;
    }
    return rc;
}

/*
 * It is the callers responsibility to free the output of this function
 */

static crm_data_t*
retrieveCib(const char *filename, const char *sigfile, gboolean archive_invalid)
{
    struct stat buf;
    FILE *cib_file = NULL;
    crm_data_t *root = NULL;
    crm_info("Reading cluster configuration from: %s (digest: %s)",
	     filename, sigfile);

    if(stat(filename, &buf) != 0) {
	crm_warn("Cluster configuration not found: %s", filename);
	return NULL;
    }

    cib_file = fopen(filename, "r");
    if(cib_file == NULL) {
	cl_perror("Could not open config file %s for reading", filename);
	
    } else {
	root = file2xml(cib_file, FALSE);
	fclose(cib_file);
    }
    
    if(root == NULL) {
	crm_err("%s exists but does NOT contain valid XML. ", filename);
	crm_warn("Continuing but %s will NOT used.", filename);
	
    } else if(validate_cib_digest(root, sigfile) == FALSE) {
	crm_err("Checksum of %s failed!  Configuration contents ignored!", filename);
	crm_err("Usually this is caused by manually changes, "
		"please refer to http://linux-ha.org/v2/faq/cib_changes_detected");
	crm_warn("Continuing but %s will NOT used.", filename);
	free_xml(root);
	root = NULL;

	if(archive_invalid) {
	    int rc = 0;
	    char *suffix = crm_itoa(getpid());
	    
	    /* Archive the original files so the contents are not lost */
	    crm_err("Archiving corrupt or unusable configuration to %s.%s", filename, suffix);
	    rc = archive_file(filename, NULL, suffix, TRUE);
	    if(rc < 0) {
		crm_err("Archival of %s failed - Disabling disk writes and continuing", filename);
		cib_writes_enabled = FALSE;
	    }

	    rc = archive_file(sigfile, NULL, suffix, TRUE);
	    if(rc < 0) {
		crm_err("Archival of %s failed - Disabling disk writes and continuing", sigfile);
		cib_writes_enabled = FALSE;
	    }
	    
	    /* Unlink the original files so they dont get in the way later */
	    cib_unlink(filename);
	    cib_unlink(sigfile);
	    crm_free(suffix);
	}
    }
    return root;
}

crm_data_t*
readCibXmlFile(const char *dir, const char *file, gboolean discard_status)
{
	gboolean dtd_ok = TRUE;

	char *filename = NULL, *sigfile = NULL;
	const char *name = NULL;
	const char *value = NULL;
	const char *ignore_dtd = NULL;
	
	crm_data_t *root = NULL;
	crm_data_t *status = NULL;

	if(!crm_is_writable(dir, file, HA_CCMUSER, NULL, FALSE)) {
		cib_status = cib_bad_permissions;
		return NULL;
	}
	
	filename = crm_concat(dir, file, '/');
	sigfile  = crm_concat(filename, "sig", '.');

	cib_status = cib_ok;
	root = retrieveCib(filename, sigfile, TRUE);
	if(root == NULL) {
	    char *tmp = NULL;
	    
	    /* Try the backups */
	    tmp = filename;
	    filename = crm_concat(tmp, "last", '.');
	    crm_free(tmp);
	    
	    tmp = sigfile;
	    sigfile = crm_concat(tmp, "last", '.');
	    crm_free(tmp);
	    
	    crm_warn("Primary configuration corrupt or unusable, trying backup...");
	    root = retrieveCib(filename, sigfile, FALSE);
	}

	if(root == NULL) {
	    root = createEmptyCib();
	    crm_warn("Continuing with an empty configuration.");
	} else {
	    crm_xml_add(root, "generated", XML_BOOLEAN_FALSE);	
	}	

	if(cib_writes_enabled && getenv("HA_VALGRIND_ENABLED") != NULL) {
		cib_writes_enabled = FALSE;
		crm_err("HA_VALGRIND_ENABLED: %s",
			getenv("HA_VALGRIND_ENABLED"));
		crm_err("*********************************************************");
		crm_err("*** Disabling disk writes to avoid confusing Valgrind ***");
		crm_err("*********************************************************");	
	}
	
	status = find_xml_node(root, XML_CIB_TAG_STATUS, FALSE);
	if(discard_status && status != NULL) {
		/* strip out the status section if there is one */
		free_xml_from_parent(root, status);
		status = NULL;
	}
	if(status == NULL) {
		create_xml_node(root, XML_CIB_TAG_STATUS);		
	}
	
	/* Do this before DTD validation happens */

	/* fill in some defaults */
	name = XML_ATTR_GENERATION_ADMIN;
	value = crm_element_value(root, name);
	if(value == NULL) {
		crm_warn("No value for %s was specified in the configuration.",
			 name);
		crm_warn("The reccomended course of action is to shutdown,"
			 " run crm_verify and fix any errors it reports.");
		crm_warn("We will default to zero and continue but may get"
			 " confused about which configuration to use if"
			 " multiple nodes are powered up at the same time.");
		crm_xml_add_int(root, name, 0);
	}
	
	name = XML_ATTR_GENERATION;
	value = crm_element_value(root, name);
	if(value == NULL) {
		crm_xml_add_int(root, name, 0);
	}
	
	name = XML_ATTR_NUMUPDATES;
	value = crm_element_value(root, name);
	if(value == NULL) {
		crm_xml_add_int(root, name, 0);
	}
	
	/* unset these and require the DC/CCM to update as needed */
	update_counters(__FILE__, __PRETTY_FUNCTION__, root);
	xml_remove_prop(root, XML_ATTR_DC_UUID);

	if(discard_status) {
		crm_log_xml_info(root, "[on-disk]");
	}
	
	ignore_dtd = crm_element_value(root, "ignore_dtd");
	dtd_ok = validate_with_dtd(root, TRUE, HA_NOARCHDATAHBDIR"/crm.dtd");
	if(dtd_ok == FALSE) {
		crm_err("CIB does not validate against "HA_NOARCHDATAHBDIR"/crm.dtd");
		if(ignore_dtd == NULL
		   && crm_is_true(ignore_dtd) == FALSE) {
			cib_status = cib_dtd_validation;
		}
		
	} else if(ignore_dtd == NULL) {
		crm_notice("Enabling DTD validation on"
			   " the existing (sane) configuration");
		crm_xml_add(root, "ignore_dtd", XML_BOOLEAN_FALSE);	
	}	
	
	if(do_id_check(root, NULL, TRUE, FALSE)) {
		crm_err("%s does not contain a vaild configuration:"
			" ID check failed",
			 filename);
		cib_status = cib_id_check;
	}

	if (verifyCibXml(root) == FALSE) {
		crm_err("%s does not contain a vaild configuration:"
			" structure test failed",
			 filename);
		cib_status = cib_bad_config;
	}

	crm_free(filename);
	crm_free(sigfile);
	return root;
}

/*
 * The caller should never free the return value
 */
crm_data_t*
get_the_CIB(void)
{
	return the_cib;
}

gboolean
uninitializeCib(void)
{
	crm_data_t *tmp_cib = the_cib;
	
	
	if(tmp_cib == NULL) {
		crm_debug("The CIB has already been deallocated.");
		return FALSE;
	}
	
	initialized = FALSE;
	the_cib = NULL;
	node_search = NULL;
	resource_search = NULL;
	constraint_search = NULL;
	status_search = NULL;

	crm_debug("Deallocating the CIB.");
	
	free_xml(tmp_cib);

	crm_debug("The CIB has been deallocated.");
	
	return TRUE;
}




/*
 * This method will not free the old CIB pointer or the new one.
 * We rely on the caller to have saved a pointer to the old CIB
 *   and to free the old/bad one depending on what is appropriate.
 */
gboolean
initializeCib(crm_data_t *new_cib)
{
	gboolean is_valid = TRUE;
	crm_data_t *tmp_node = NULL;

	if(new_cib == NULL) {
		return FALSE;
	}
	
	xml_validate(new_cib);

	tmp_node = get_object_root(XML_CIB_TAG_NODES, new_cib);
	if (tmp_node == NULL) { is_valid = FALSE; }

	tmp_node = get_object_root(XML_CIB_TAG_RESOURCES, new_cib);
	if (tmp_node == NULL) { is_valid = FALSE; }

	tmp_node = get_object_root(XML_CIB_TAG_CONSTRAINTS, new_cib);
	if (tmp_node == NULL) { is_valid = FALSE; }

	tmp_node = get_object_root(XML_CIB_TAG_CRMCONFIG, new_cib);
	if (tmp_node == NULL) { is_valid = FALSE; }

	tmp_node = get_object_root(XML_CIB_TAG_STATUS, new_cib);
	if (is_valid && tmp_node == NULL) {
		create_xml_node(new_cib, XML_CIB_TAG_STATUS);
	}

	if(is_valid == FALSE) {
		crm_warn("CIB Verification failed");
		return FALSE;
	}

	update_counters(__FILE__, __PRETTY_FUNCTION__, new_cib);
	
	the_cib = new_cib;
	initialized = TRUE;
	return TRUE;
}

int
archive_file(const char *oldname, const char *newname, const char *ext, gboolean preserve)
{
	/* move 'oldname' to 'newname' by creating a hard link to it
	 *  and then removing the original hard link
	 */
	int rc = 0;
	int res = 0;
	struct stat tmp;
	int s_res = 0;
	char *backup_file = NULL;
	static const char *back_ext = "bak";

	/* calculate the backup name if required */
	if(newname != NULL) {
		backup_file = crm_strdup(newname);

	} else {
		int max_name_len = 1024;
		crm_malloc0(backup_file, max_name_len);
		if (ext == NULL) {
			ext = back_ext;
		}
		snprintf(backup_file, max_name_len - 1, "%s.%s", oldname, ext);
	}

	if(backup_file == NULL || strlen(backup_file) == 0) {
		crm_err("%s backup filename was %s",
			newname == NULL?"calculated":"supplied",
			backup_file == NULL?"null":"empty");
		rc = -4;		
	}
	
	s_res = stat(backup_file, &tmp);
	
	/* move the old backup */
	if (rc == 0 && s_res >= 0) {
		if(preserve == FALSE) {
			res = unlink(backup_file);
			if (res < 0) {
				cl_perror("Could not unlink %s", backup_file);
				rc = -1;
			}
		} else {
			crm_info("Archive file %s exists... backing it up first", backup_file);
			res = archive_file(backup_file, NULL, NULL, preserve);
			if (res < 0) {
				return res;
			}
		}
	}
    
	s_res = stat(oldname, &tmp);

	/* copy */
	if (rc == 0 && s_res >= 0) {
		res = link(oldname, backup_file);
		if (res < 0) {
			cl_perror("Could not create backup %s from %s",
				  backup_file, oldname);
			rc = -2;

		} else if(preserve) {
			crm_info("%s archived as %s", oldname, backup_file);

		} else {
			crm_debug("%s archived as %s", oldname, backup_file);
		}
	}
	crm_free(backup_file);
	return rc;
    
}

/*
 * This method will free the old CIB pointer on success and the new one
 * on failure.
 */
int
activateCibXml(crm_data_t *new_cib, gboolean to_disk)
{
	int error_code = cib_ok;
	crm_data_t *saved_cib = the_cib;
	const char *ignore_dtd = NULL;

	crm_log_xml_debug_4(new_cib, "Attempting to activate CIB");

	CRM_ASSERT(new_cib != saved_cib);
	if(saved_cib != NULL) {
		crm_validate_data(saved_cib);
	}

	ignore_dtd = crm_element_value(new_cib, "ignore_dtd");
	if(
#if CRM_DEPRECATED_SINCE_2_0_4
	   ignore_dtd != NULL &&
#endif
	   crm_is_true(ignore_dtd) == FALSE
	   && validate_with_dtd(
		   new_cib, TRUE, HA_NOARCHDATAHBDIR"/crm.dtd") == FALSE) {
		crm_err("Updated CIB does not validate against "HA_NOARCHDATAHBDIR"/crm.dtd... ignoring");
 		error_code = cib_dtd_validation;
	}

	if(error_code == cib_ok && initializeCib(new_cib) == FALSE) {
		error_code = cib_ACTIVATION;
		crm_err("Ignoring invalid or NULL CIB");
	}

	if(error_code != cib_ok) {
		if(saved_cib != NULL) {
			crm_warn("Reverting to last known CIB");
			if (initializeCib(saved_cib) == FALSE) {
				/* oh we are so dead  */
				crm_crit("Couldn't re-initialize the old CIB!");
				cl_flush_logs();
				exit(1);
			}
			
		} else {
			crm_crit("Could not write out new CIB and no saved"
				 " version to revert to");
		}
		
	} else if(per_action_cib && cib_writes_enabled && cib_status == cib_ok) {
		crm_err("Per-action CIB");
		write_cib_contents(the_cib);
		
	} else if(cib_writes_enabled && cib_status == cib_ok && to_disk) {
		crm_debug_2("Triggering CIB write");
		G_main_set_trigger(cib_writer);
	}
	
	if(the_cib != saved_cib && the_cib != new_cib) {
		CRM_DEV_ASSERT(error_code != cib_ok);
		CRM_DEV_ASSERT(the_cib == NULL);
	}
	
	if(the_cib != new_cib) {
		free_xml(new_cib);
		CRM_DEV_ASSERT(error_code != cib_ok);
	}

	if(the_cib != saved_cib) {
		free_xml(saved_cib);
	}
	
	return error_code;
    
}

int
write_cib_contents(gpointer p) 
{
	int rc = 0;
	gboolean need_archive = FALSE;
	struct stat buf;
	char *digest = NULL;
	int exit_rc = LSB_EXIT_OK;
	crm_data_t *cib_status_root = NULL;

	/* we can scribble on "the_cib" here and not affect the parent */
	const char *epoch = crm_element_value(the_cib, XML_ATTR_GENERATION);
	const char *updates = crm_element_value(the_cib, XML_ATTR_NUMUPDATES);
	const char *admin_epoch = crm_element_value(
		the_cib, XML_ATTR_GENERATION_ADMIN);

	need_archive = (stat(CIB_FILENAME, &buf) == 0);
	if (need_archive) {
	    crm_debug("Archiving current version");	    

	    /* check the admin didnt modify it underneath us */
	    if(validate_on_disk_cib(CIB_FILENAME, NULL) == FALSE) {
		crm_err("%s was manually modified while Heartbeat was active!",
			CIB_FILENAME);
		exit_rc = LSB_EXIT_GENERIC;
		goto cleanup;
	    }

	    /* These calls leak, but we're in a separate process that will exit
	     * when the function does... so it's of no consequence
	     */
	    CRM_ASSERT(retrieveCib(CIB_FILENAME, CIB_FILENAME".sig", FALSE) != NULL);
	    
	    rc = archive_file(CIB_FILENAME, NULL, "last", FALSE);
	    if(rc != 0) {
		crm_err("Could not make backup of the existing CIB: %d", rc);
		exit_rc = LSB_EXIT_GENERIC;
		goto cleanup;
	    }
	
	    rc = archive_file(CIB_FILENAME".sig", NULL, "last", FALSE);
	    if(rc != 0) {
		crm_warn("Could not make backup of the existing CIB digest: %d",
			 rc);
	    }

	    CRM_ASSERT(retrieveCib(CIB_FILENAME, CIB_FILENAME".sig", FALSE) != NULL);
	    CRM_ASSERT(retrieveCib(CIB_FILENAME".last", CIB_FILENAME".sig.last", FALSE) != NULL);
	    crm_debug("Verified CIB archive");	    
	}
	
	/* Given that we discard the status section on startup
	 *   there is no point writing it out in the first place
	 *   since users just get confused by it
	 *
	 * Although, it does help me once in a while
	 *
	 * So delete the status section before we write it out
	 */
	if(p == NULL) {
	    cib_status_root = find_xml_node(the_cib, XML_CIB_TAG_STATUS, TRUE);
	    CRM_DEV_ASSERT(cib_status_root != NULL);
	    
	    if(cib_status_root != NULL) {
		free_xml_from_parent(the_cib, cib_status_root);
	    }
	}
	
	rc = write_xml_file(the_cib, CIB_FILENAME, FALSE);
	crm_debug("Wrote CIB to disk");
	if(rc <= 0) {
		crm_err("Changes couldn't be written to disk");
		exit_rc = LSB_EXIT_GENERIC;
		goto cleanup;
	}

	digest = calculate_xml_digest(the_cib, FALSE, FALSE);
	crm_info("Wrote version %s.%s.%s of the CIB to disk (digest: %s)",
		 admin_epoch?admin_epoch:"0",
		 epoch?epoch:"0", updates?updates:"0", digest);	
	
	rc = write_cib_digest(the_cib, digest);
	crm_debug("Wrote digest to disk");

	if(rc <= 0) {
		crm_err("Digest couldn't be written to disk");
		exit_rc = LSB_EXIT_GENERIC;
		goto cleanup;
	}

	CRM_ASSERT(retrieveCib(CIB_FILENAME, CIB_FILENAME".sig", FALSE) != NULL);
	if(need_archive) {
	    CRM_ASSERT(retrieveCib(CIB_FILENAME".last", CIB_FILENAME".sig.last", FALSE) != NULL);
	}

	crm_debug("Wrote and verified CIB");

  cleanup:
	crm_free(digest);

	if(p == NULL) {
		/* fork-and-write mode */
		exit(exit_rc);
	}

	/* stand-alone mode */
	return exit_rc;
}

gboolean
set_transition(crm_data_t *xml_obj)
{
	const char *current = NULL;
	if(xml_obj == NULL) {
		return FALSE;
	}

	current = crm_element_value(xml_obj, XML_ATTR_CCM_TRANSITION);
	if(safe_str_neq(current, ccm_transition_id)) {
		crm_debug("CCM transition: old=%s, new=%s",
			  current, ccm_transition_id);
		crm_xml_add(xml_obj, XML_ATTR_CCM_TRANSITION,ccm_transition_id);
		return TRUE;
	}
	return FALSE;
}

gboolean
set_connected_peers(crm_data_t *xml_obj)
{
	int active = 0;
	int current = 0;
	char *peers_s = NULL;
	const char *current_s = NULL;
	if(xml_obj == NULL) {
		return FALSE;
	}
	
	current_s = crm_element_value(xml_obj, XML_ATTR_NUMPEERS);
	g_hash_table_foreach(peer_hash, GHFunc_count_peers, &active);
	current = crm_parse_int(current_s, "0");
	if(current != active) {
		peers_s = crm_itoa(active);
		crm_xml_add(xml_obj, XML_ATTR_NUMPEERS, peers_s);
		crm_debug("We now have %s active peers", peers_s);
		crm_free(peers_s);
		return TRUE;
	}
	return FALSE;
}

gboolean
update_quorum(crm_data_t *xml_obj) 
{
	const char *quorum_value = XML_BOOLEAN_FALSE;
	const char *current = NULL;
	if(xml_obj == NULL) {
		return FALSE;
	}
	
	current = crm_element_value(xml_obj, XML_ATTR_HAVE_QUORUM);
	if(cib_have_quorum) {
		quorum_value = XML_BOOLEAN_TRUE;
	}
	if(safe_str_neq(current, quorum_value)) {
		crm_debug("CCM quorum: old=%s, new=%s",
			  current, quorum_value);
		crm_xml_add(xml_obj, XML_ATTR_HAVE_QUORUM, quorum_value);
		return TRUE;
	}
	return FALSE;
}


gboolean
update_counters(const char *file, const char *fn, crm_data_t *xml_obj) 
{
	gboolean did_update = FALSE;

	did_update = did_update || update_quorum(xml_obj);
	did_update = did_update || set_transition(xml_obj);
	did_update = did_update || set_connected_peers(xml_obj);
	
	if(did_update) {
		do_crm_log(LOG_DEBUG, "Counters updated by %s", fn);
	}
	return did_update;
}



void GHFunc_count_peers(gpointer key, gpointer value, gpointer user_data)
{
	int *active = user_data;
	if(safe_str_eq(value, ONLINESTATUS)) {
		(*active)++;
		
	} else if(safe_str_eq(value, JOINSTATUS)) {
		(*active)++;
	}
}

