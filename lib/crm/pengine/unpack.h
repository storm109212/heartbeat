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
#ifndef PENGINE_UNPACK__H
#define PENGINE_UNPACK__H

extern gboolean unpack_resources(
	crm_data_t *xml_resources, pe_working_set_t *data_set);

extern gboolean unpack_config(crm_data_t *config, pe_working_set_t *data_set);

extern gboolean unpack_nodes(crm_data_t *xml_nodes, pe_working_set_t *data_set);

extern gboolean unpack_status(crm_data_t *status, pe_working_set_t *data_set);

extern gint sort_op_by_callid(gconstpointer a, gconstpointer b);

extern gboolean unpack_lrm_resources(
	node_t *node, crm_data_t * lrm_state, pe_working_set_t *data_set);

extern gboolean add_node_attrs(
	crm_data_t * attrs, node_t *node, pe_working_set_t *data_set);

extern gboolean unpack_rsc_op(
	resource_t *rsc, node_t *node, crm_data_t *xml_op,
	int *max_call_id, enum action_fail_response *failed, pe_working_set_t *data_set);

extern gboolean determine_online_status(
	crm_data_t * node_state, node_t *this_node, pe_working_set_t *data_set);

extern const char *param_value(
	GHashTable *hash, crm_data_t * parent, const char *name);


/*
 * The man pages for both curses and ncurses suggest inclusion of "curses.h".
 * We believe the following to be acceptable and portable.
 */

#if defined(HAVE_LIBNCURSES) || defined(HAVE_LIBCURSES)
#  if defined(HAVE_NCURSES_H) && !defined(HAVE_INCOMPATIBLE_PRINTW)
#    include <ncurses.h>
#    define CURSES_ENABLED 1
#  elif defined(HAVE_NCURSES_NCURSES_H) && !defined(HAVE_INCOMPATIBLE_PRINTW)
#    include <ncurses/ncurses.h>
#    define CURSES_ENABLED 1
#  elif defined(HAVE_CURSES_H) && !defined(HAVE_INCOMPATIBLE_PRINTW)
#    include <curses.h>
#    define CURSES_ENABLED 1
#  elif defined(HAVE_CURSES_CURSES_H) && !defined(HAVE_INCOMPATIBLE_PRINTW)
#    include <curses/curses.h>
#    define CURSES_ENABLED 1
#  else
#    define CURSES_ENABLED 0
#  endif
#else
#  define CURSES_ENABLED 0
#endif

#if CURSES_ENABLED
#  define status_printw(fmt, args...) printw(fmt, ##args)
#else
#  define status_printw(fmt, args...) \
	crm_err("printw support requires ncurses to be available during configure"); \
	do_crm_log(LOG_WARNING, fmt, ##args);
#endif

#define status_print(fmt, args...)			\
	if(options & pe_print_html) {			\
		FILE *stream = print_data;		\
		fprintf(stream, fmt, ##args);		\
	} else if(options & pe_print_ncurses) {		\
		status_printw(fmt, ##args);		\
	} else if(options & pe_print_printf) {		\
		FILE *stream = print_data;		\
		fprintf(stream, fmt, ##args);		\
	} else if(options & pe_print_log) {		\
		int log_level = *(int*)print_data;	\
		do_crm_log(log_level, fmt, ##args);	\
	}

#endif
