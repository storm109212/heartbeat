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

#include <crm/crm.h>
#include <crm/cib.h>
#include <crm/msg_xml.h>
#include <crm/common/xml.h>
#include <crm/common/msg.h>
#include <clplumbing/cl_misc.h>

#include <glib.h>

#include <crm/pengine/status.h>
#include <pengine.h>
#include <allocate.h>
#include <utils.h>
#include <lib/crm/pengine/utils.h>

gboolean 
unpack_constraints(crm_data_t * xml_constraints, pe_working_set_t *data_set)
{
	crm_data_t *lifetime = NULL;
	xml_child_iter(
		xml_constraints, xml_obj, 

		const char *id = crm_element_value(xml_obj, XML_ATTR_ID);
		if(id == NULL) {
			crm_config_err("Constraint <%s...> must have an id",
				crm_element_name(xml_obj));
			continue;
		}

		crm_debug_3("Processing constraint %s %s",
			    crm_element_name(xml_obj),id);

		lifetime = cl_get_struct(xml_obj, "lifetime");

		if(test_ruleset(lifetime, NULL, data_set->now) == FALSE) {
			crm_info("Constraint %s %s is not active",
				 crm_element_name(xml_obj), id);

		} else if(safe_str_eq(XML_CONS_TAG_RSC_ORDER,
				      crm_element_name(xml_obj))) {
			unpack_rsc_order(xml_obj, data_set);

		} else if(safe_str_eq(XML_CONS_TAG_RSC_DEPEND,
				      crm_element_name(xml_obj))) {
			unpack_rsc_colocation(xml_obj, data_set);

		} else if(safe_str_eq(XML_CONS_TAG_RSC_LOCATION,
				      crm_element_name(xml_obj))) {
			unpack_rsc_location(xml_obj, data_set);

		} else {
			pe_err("Unsupported constraint type: %s",
				crm_element_name(xml_obj));
		}
		);

	return TRUE;
}

static const char *
invert_action(const char *action) 
{
	if(safe_str_eq(action, CRMD_ACTION_START)) {
		return CRMD_ACTION_STOP;

	} else if(safe_str_eq(action, CRMD_ACTION_STOP)) {
		return CRMD_ACTION_START;
		
	} else if(safe_str_eq(action, CRMD_ACTION_PROMOTE)) {
		return CRMD_ACTION_DEMOTE;
		
 	} else if(safe_str_eq(action, CRMD_ACTION_DEMOTE)) {
		return CRMD_ACTION_PROMOTE;

	} else if(safe_str_eq(action, CRMD_ACTION_PROMOTED)) {
		return CRMD_ACTION_DEMOTED;
		
	} else if(safe_str_eq(action, CRMD_ACTION_DEMOTED)) {
		return CRMD_ACTION_PROMOTED;

	} else if(safe_str_eq(action, CRMD_ACTION_STARTED)) {
		return CRMD_ACTION_STOPPED;
		
	} else if(safe_str_eq(action, CRMD_ACTION_STOPPED)) {
		return CRMD_ACTION_STARTED;
	}
	crm_config_warn("Unknown action: %s", action);
	return NULL;
}

gboolean
unpack_rsc_order(crm_data_t * xml_obj, pe_working_set_t *data_set)
{
	int score_i = 0;
	int order_id = 0;
	resource_t *rsc_lh = NULL;
	resource_t *rsc_rh = NULL;
	gboolean symmetrical_bool = TRUE;
	enum pe_ordering cons_weight = pe_order_optional;

	const char *id_rh  = NULL;
	const char *id_lh  = NULL;
	const char *action = NULL;
	const char *action_rh = NULL;
	
	const char *id     = crm_element_value(xml_obj, XML_ATTR_ID);
	const char *type   = crm_element_value(xml_obj, XML_ATTR_TYPE);
	const char *score  = crm_element_value(xml_obj, XML_RULE_ATTR_SCORE);
	const char *symmetrical = crm_element_value(
		xml_obj, XML_CONS_ATTR_SYMMETRICAL);

	cl_str_to_boolean(symmetrical, &symmetrical_bool);
	
	if(xml_obj == NULL) {
		crm_config_err("No constraint object to process.");
		return FALSE;

	} else if(id == NULL) {
		crm_config_err("%s constraint must have an id",
			crm_element_name(xml_obj));
		return FALSE;
		
	}

	id_lh  = crm_element_value(xml_obj, XML_CONS_ATTR_TO);
	id_rh  = crm_element_value(xml_obj, XML_CONS_ATTR_FROM);
	action = crm_element_value(xml_obj, XML_CONS_ATTR_ACTION);
	action_rh = crm_element_value(xml_obj, XML_CONS_ATTR_TOACTION);
	if(action == NULL) {
	    action = CRMD_ACTION_START;
	}
	if(action_rh == NULL) {
	    action_rh = action;
	}

	if(safe_str_neq(type, "before")) {
	    /* normalize the input - swap everything over */
	    const char *tmp = NULL;
	    type = "before";
	    tmp = id_rh; id_rh = id_lh; id_lh = tmp;
	    tmp = action_rh; action_rh = action; action = tmp;
	}

	if(id_lh == NULL || id_rh == NULL) {
		crm_config_err("Constraint %s needs two sides lh: %s rh: %s",
			      id, crm_str(id_lh), crm_str(id_rh));
		return FALSE;
	}	
	
	rsc_lh = pe_find_resource(data_set->resources, id_rh);
	rsc_rh = pe_find_resource(data_set->resources, id_lh);

	if(rsc_lh == NULL) {
		crm_config_err("Constraint %s: no resource found for LHS (%s)", id, id_rh);
		return FALSE;
	
	} else if(rsc_rh == NULL) {
		crm_config_err("Constraint %s: no resource found for RHS of (%s)", id, id_lh);
		return FALSE;
	}

	if(score == NULL) {
	    score = "INFINITY";
	}
	
	score_i = char2score(score);
	cons_weight = pe_order_optional;
	if(score_i == 0 && rsc_rh->restart_type == pe_restart_restart) {
		crm_debug_2("Upgrade : recovery - implies right");
 		cons_weight |= pe_order_implies_right;
	}
	
	if(score_i < 0) {
		crm_debug_2("Upgrade : implies left");
 		cons_weight |= pe_order_implies_left;

	} else if(score_i > 0) {
		crm_debug_2("Upgrade : implies right");
 		cons_weight |= pe_order_implies_right;
		if(safe_str_eq(action, CRMD_ACTION_START)
		   || safe_str_eq(action, CRMD_ACTION_PROMOTE)) {
			crm_debug_2("Upgrade : runnable");
			cons_weight |= pe_order_runnable_left;
		}
	}
	
	order_id = custom_action_order(
		rsc_lh, generate_op_key(rsc_lh->id, action, 0), NULL,
		rsc_rh, generate_op_key(rsc_rh->id, action_rh, 0), NULL,
		cons_weight, data_set);

	crm_debug("order-%d (%s): %s_%s %s %s_%s flags=0x%.6x",
		  order_id, id, rsc_lh->id, action, type, rsc_rh->id, action_rh,
		  cons_weight);
	
	
	if(symmetrical_bool == FALSE) {
		return TRUE;
	}
	
	action = invert_action(action);
	action_rh = invert_action(action_rh);

	cons_weight = pe_order_optional;
	if(score_i == 0 && rsc_rh->restart_type == pe_restart_restart) {
		crm_debug_2("Upgrade : recovery - implies left");
 		cons_weight |= pe_order_implies_left;
	}
	
	score_i *= -1;
	if(score_i < 0) {
		crm_debug_2("Upgrade : implies left");
 		cons_weight |= pe_order_implies_left;
		if(safe_str_eq(action_rh, CRMD_ACTION_DEMOTE)) {
			crm_debug_2("Upgrade : demote");
			cons_weight |= pe_order_demote;
		}
		
	} else if(score_i > 0) {
		crm_debug_2("Upgrade : implies right");
 		cons_weight |= pe_order_implies_right;
		if(safe_str_eq(action, CRMD_ACTION_START)
		   || safe_str_eq(action, CRMD_ACTION_PROMOTE)) {
			crm_debug_2("Upgrade : runnable");
			cons_weight |= pe_order_runnable_left;
		}
	}

	if(action == NULL || action_rh == NULL) {
		crm_config_err("Cannot invert rsc_order constraint %s."
			       " Please specify the inverse manually.", id);
		return TRUE;
	}
	
	order_id = custom_action_order(
		rsc_rh, generate_op_key(rsc_rh->id, action_rh, 0), NULL,
		rsc_lh, generate_op_key(rsc_lh->id, action, 0), NULL,
		cons_weight, data_set);
	crm_debug("order-%d (%s): %s_%s %s %s_%s flags=0x%.6x",
		  order_id, id, rsc_rh->id, action_rh, type, rsc_lh->id, action,
		  cons_weight);
	
	return TRUE;
}

gboolean
unpack_rsc_location(crm_data_t * xml_obj, pe_working_set_t *data_set)
{
	gboolean empty = TRUE;
	const char *id_lh   = crm_element_value(xml_obj, "rsc");
	const char *id      = crm_element_value(xml_obj, XML_ATTR_ID);
	resource_t *rsc_lh  = pe_find_resource(data_set->resources, id_lh);
	const char *node    = crm_element_value(xml_obj, "node");
	const char *score   = crm_element_value(xml_obj, XML_RULE_ATTR_SCORE);
	
	if(rsc_lh == NULL) {
		/* only a warn as BSC adds the constraint then the resource */
		crm_config_warn("No resource (con=%s, rsc=%s)", id, id_lh);
		return FALSE;

	} else if(is_not_set(rsc_lh->flags, pe_rsc_managed)) {
		crm_debug_2("Ignoring constraint %s: resource %s not managed",
			    id, id_lh);
		return FALSE;
	}

	if(node != NULL && score != NULL) {
	    int score_i = char2score(score);
	    node_t *match = pe_find_node(data_set->nodes, node);

	    if(match) {
		rsc2node_new(id, rsc_lh, score_i, match, data_set);
		return TRUE;
	    } else {
		return FALSE;
	    }
	}
	
	xml_child_iter_filter(
		xml_obj, rule_xml, XML_TAG_RULE,
		empty = FALSE;
		crm_debug_2("Unpacking %s/%s", id, ID(rule_xml));
		generate_location_rule(rsc_lh, rule_xml, data_set);
		);

	if(empty) {
		crm_config_err("Invalid location constraint %s:"
			      " rsc_location must contain at least one rule",
			      ID(xml_obj));
	}
	return TRUE;
}

static int
get_node_score(const char *rule, const char *score, gboolean raw, node_t *node)
{
	int score_f = 0;
	if(score == NULL) {
		pe_err("Rule %s: no score specified.  Assuming 0.", rule);
	
	} else if(raw) {
		score_f = char2score(score);
	
	} else {
		const char *attr_score = g_hash_table_lookup(
			node->details->attrs, score);
		if(attr_score == NULL) {
			crm_debug("Rule %s: node %s did not have a value for %s",
				  rule, node->details->uname, score);
			score_f = -INFINITY;
			
		} else {
			crm_debug("Rule %s: node %s had value %s for %s",
				  rule, node->details->uname, attr_score, score);
			score_f = char2score(attr_score);
		}
	}
	return score_f;
}


rsc_to_node_t *
generate_location_rule(
	resource_t *rsc, crm_data_t *rule_xml, pe_working_set_t *data_set)
{	
	const char *rule_id = NULL;
	const char *score   = NULL;
	const char *boolean = NULL;
	const char *role    = NULL;

	GListPtr match_L  = NULL;
	
	int score_f   = 0;
	gboolean do_and = TRUE;
	gboolean accept = TRUE;
	gboolean raw_score = TRUE;
	
	rsc_to_node_t *location_rule = NULL;
	
	rule_id = crm_element_value(rule_xml, XML_ATTR_ID);
	boolean = crm_element_value(rule_xml, XML_RULE_ATTR_BOOLEAN_OP);
	role = crm_element_value(rule_xml, XML_RULE_ATTR_ROLE);

	crm_debug_2("Processing rule: %s", rule_id);

	if(role != NULL && text2role(role) == RSC_ROLE_UNKNOWN) {
		pe_err("Bad role specified for %s: %s", rule_id, role);
		return NULL;
	}
	
	score = crm_element_value(rule_xml, XML_RULE_ATTR_SCORE);
	if(score != NULL) {
		score_f = char2score(score);
		
	} else {
		score = crm_element_value(
			rule_xml, XML_RULE_ATTR_SCORE_ATTRIBUTE);
		if(score == NULL) {
			score = crm_element_value(
				rule_xml, XML_RULE_ATTR_SCORE_MANGLED);
		}
		if(score != NULL) {
			raw_score = FALSE;
		}
	}
	if(safe_str_eq(boolean, "or")) {
		do_and = FALSE;
	}
	
	location_rule = rsc2node_new(rule_id, rsc, 0, NULL, data_set);
	
	if(location_rule == NULL) {
		return NULL;
	}
	if(role != NULL) {
		crm_debug_2("Setting role filter: %s", role);
		location_rule->role_filter = text2role(role);
	}
	if(do_and) {
		match_L = node_list_dup(data_set->nodes, TRUE, FALSE);
		slist_iter(
			node, node_t, match_L, lpc,
			node->weight = get_node_score(rule_id, score, raw_score, node);
			);
	}

	xml_child_iter(
		rule_xml, expr, 		

		enum expression_type type = find_expression_type(expr);
		crm_debug_2("Processing expression: %s", ID(expr));

		if(type == not_expr) {
			pe_err("Expression <%s id=%s...> is not valid",
			       crm_element_name(expr), crm_str(ID(expr)));
			continue;	
		}	
		
		slist_iter(
			node, node_t, data_set->nodes, lpc,

			if(type == nested_rule) {
				accept = test_rule(
					expr, node->details->attrs,
					RSC_ROLE_UNKNOWN, data_set->now);
			} else {
				accept = test_expression(
					expr, node->details->attrs,
					RSC_ROLE_UNKNOWN, data_set->now);
			}

			score_f = get_node_score(rule_id, score, raw_score, node);
/* 			if(accept && score_f == -INFINITY) { */
/* 				accept = FALSE; */
/* 			} */
			
			if(accept) {
				node_t *local = pe_find_node_id(
					match_L, node->details->id);
				if(local == NULL && do_and) {
					continue;
					
				} else if(local == NULL) {
					local = node_copy(node);
					match_L = g_list_append(match_L, local);
				}

				if(do_and == FALSE) {
					local->weight = merge_weights(
						local->weight, score_f);
				}
				crm_debug_2("node %s now has weight %d",
					    node->details->uname, local->weight);
				
			} else if(do_and && !accept) {
				/* remove it */
				node_t *delete = pe_find_node_id(
					match_L, node->details->id);
				if(delete != NULL) {
					match_L = g_list_remove(match_L,delete);
					crm_debug_5("node %s did not match",
						    node->details->uname);
				}
				crm_free(delete);
			}
			);
		);
	
	location_rule->node_list_rh = match_L;
	if(location_rule->node_list_rh == NULL) {
		crm_debug_2("No matching nodes for rule %s", rule_id);
		return NULL;
	} 

	crm_debug_3("%s: %d nodes matched",
		    rule_id, g_list_length(location_rule->node_list_rh));
	return location_rule;
}

static gint sort_cons_priority_lh(gconstpointer a, gconstpointer b)
{
	const rsc_colocation_t *rsc_constraint1 = (const rsc_colocation_t*)a;
	const rsc_colocation_t *rsc_constraint2 = (const rsc_colocation_t*)b;

	if(a == NULL) { return 1; }
	if(b == NULL) { return -1; }

	CRM_ASSERT(rsc_constraint1->rsc_lh != NULL);
	CRM_ASSERT(rsc_constraint1->rsc_rh != NULL);
	
	if(rsc_constraint1->rsc_lh->priority > rsc_constraint2->rsc_lh->priority) {
	    return -1;
	}
	
	if(rsc_constraint1->rsc_lh->priority < rsc_constraint2->rsc_lh->priority) {
	    return 1;
	}

	return strcmp(rsc_constraint1->rsc_lh->id, rsc_constraint2->rsc_lh->id);
}

static gint sort_cons_priority_rh(gconstpointer a, gconstpointer b)
{
	const rsc_colocation_t *rsc_constraint1 = (const rsc_colocation_t*)a;
	const rsc_colocation_t *rsc_constraint2 = (const rsc_colocation_t*)b;

	if(a == NULL) { return 1; }
	if(b == NULL) { return -1; }

	CRM_ASSERT(rsc_constraint1->rsc_lh != NULL);
	CRM_ASSERT(rsc_constraint1->rsc_rh != NULL);
	
	if(rsc_constraint1->rsc_rh->priority > rsc_constraint2->rsc_rh->priority) {
	    return -1;
	}
	
	if(rsc_constraint1->rsc_rh->priority < rsc_constraint2->rsc_rh->priority) {
	    return 1;
	}
	return strcmp(rsc_constraint1->rsc_rh->id, rsc_constraint2->rsc_rh->id);
}

gboolean
rsc_colocation_new(const char *id, const char *node_attr, int score,
		   resource_t *rsc_lh, resource_t *rsc_rh,
		   const char *state_lh, const char *state_rh,
		   pe_working_set_t *data_set)
{
	rsc_colocation_t *new_con      = NULL;

	if(rsc_lh == NULL){
		crm_config_err("No resource found for LHS %s", id);
		return FALSE;

	} else if(rsc_rh == NULL){
		crm_config_err("No resource found for RHS of %s", id);
		return FALSE;
	}

	crm_malloc0(new_con, sizeof(rsc_colocation_t));
	if(new_con == NULL) {
		return FALSE;
	}

	if(state_lh == NULL
	   || safe_str_eq(state_lh, RSC_ROLE_STARTED_S)) {
		state_lh = RSC_ROLE_UNKNOWN_S;
	}

	if(state_rh == NULL
	   || safe_str_eq(state_rh, RSC_ROLE_STARTED_S)) {
		state_rh = RSC_ROLE_UNKNOWN_S;
	} 

	new_con->id       = id;
	new_con->rsc_lh   = rsc_lh;
	new_con->rsc_rh   = rsc_rh;
	new_con->score   = score;
	new_con->role_lh = text2role(state_lh);
	new_con->role_rh = text2role(state_rh);
	new_con->node_attribute = node_attr;
	
	crm_debug_4("Adding constraint %s (%p) to %s",
		  new_con->id, new_con, rsc_lh->id);
	
	rsc_lh->rsc_cons = g_list_insert_sorted(
		rsc_lh->rsc_cons, new_con, sort_cons_priority_rh);

	rsc_rh->rsc_cons_lhs = g_list_insert_sorted(
		rsc_rh->rsc_cons_lhs, new_con, sort_cons_priority_lh);

	data_set->colocation_constraints = g_list_append(
		data_set->colocation_constraints, new_con);
	
	return TRUE;
}

/* LHS before RHS */
int
custom_action_order(
	resource_t *lh_rsc, char *lh_action_task, action_t *lh_action,
	resource_t *rh_rsc, char *rh_action_task, action_t *rh_action,
	enum pe_ordering type, pe_working_set_t *data_set)
{
	order_constraint_t *order = NULL;
	if(lh_rsc == NULL && lh_action) {
		lh_rsc = lh_action->rsc;
	}
	if(rh_rsc == NULL && rh_action) {
		rh_rsc = rh_action->rsc;
	}

	if((lh_action == NULL && lh_rsc == NULL)
	   || (rh_action == NULL && rh_rsc == NULL)){
		crm_config_err("Invalid inputs %p.%p %p.%p",
			      lh_rsc, lh_action, rh_rsc, rh_action);
		crm_free(lh_action_task);
		crm_free(rh_action_task);
		return -1;
	}
	
	crm_malloc0(order, sizeof(order_constraint_t));

	crm_debug_3("Creating ordering constraint %d",
		    data_set->order_id);
	
	order->id             = data_set->order_id++;
	order->type           = type;
	order->lh_rsc         = lh_rsc;
	order->rh_rsc         = rh_rsc;
	order->lh_action      = lh_action;
	order->rh_action      = rh_action;
	order->lh_action_task = lh_action_task;
	order->rh_action_task = rh_action_task;
	
	data_set->ordering_constraints = g_list_append(
		data_set->ordering_constraints, order);
	
	if(lh_rsc != NULL && rh_rsc != NULL) {
		crm_debug_4("Created ordering constraint %d (%s):"
			 " %s/%s before %s/%s",
			 order->id, ordering_type2text(order->type),
			 lh_rsc->id, lh_action_task,
			 rh_rsc->id, rh_action_task);
		
	} else if(lh_rsc != NULL) {
		crm_debug_4("Created ordering constraint %d (%s):"
			 " %s/%s before action %d (%s)",
			 order->id, ordering_type2text(order->type),
			 lh_rsc->id, lh_action_task,
			 rh_action->id, rh_action_task);
		
	} else if(rh_rsc != NULL) {
		crm_debug_4("Created ordering constraint %d (%s):"
			 " action %d (%s) before %s/%s",
			 order->id, ordering_type2text(order->type),
			 lh_action->id, lh_action_task,
			 rh_rsc->id, rh_action_task);
		
	} else {
		crm_debug_4("Created ordering constraint %d (%s):"
			 " action %d (%s) before action %d (%s)",
			 order->id, ordering_type2text(order->type),
			 lh_action->id, lh_action_task,
			 rh_action->id, rh_action_task);
	}
	
	return order->id;
}

gboolean
unpack_rsc_colocation(crm_data_t * xml_obj, pe_working_set_t *data_set)
{
	int score_i = 0;
	const char *id    = crm_element_value(xml_obj, XML_ATTR_ID);
	const char *id_rh = crm_element_value(xml_obj, XML_CONS_ATTR_TO);
	const char *id_lh = crm_element_value(xml_obj, XML_CONS_ATTR_FROM);
	const char *score = crm_element_value(xml_obj, XML_RULE_ATTR_SCORE);
	const char *state_lh = crm_element_value(xml_obj, XML_RULE_ATTR_FROMSTATE);
	const char *state_rh = crm_element_value(xml_obj, XML_RULE_ATTR_TOSTATE);
	const char *attr = crm_element_value(xml_obj, "node_attribute");
	const char *symmetrical = crm_element_value(xml_obj, XML_CONS_ATTR_SYMMETRICAL);


	resource_t *rsc_lh = pe_find_resource(data_set->resources, id_lh);
	resource_t *rsc_rh = pe_find_resource(data_set->resources, id_rh);
 
	if(rsc_lh == NULL) {
		crm_config_err("No resource (con=%s, rsc=%s)", id, id_lh);
		return FALSE;
		
	} else if(rsc_rh == NULL) {
		crm_config_err("No resource (con=%s, rsc=%s)", id, id_rh);
		return FALSE;
	}

	if(score) {
		score_i = char2score(score);
	}

	rsc_colocation_new(
	    id, attr, score_i, rsc_lh, rsc_rh, state_lh, state_rh, data_set);
	
	if(crm_is_true(symmetrical)) {
		rsc_colocation_new(
			id, attr, score_i, rsc_rh, rsc_lh, state_rh, state_lh, data_set);
	}
	return TRUE;
}

gboolean is_active(rsc_to_node_t *cons)
{
	return TRUE;
}
