//
// $Id$
//

// ============================================================================
//
// = LIBRARY
//    TAO IDL
//
// = FILENAME
//    be_visitor_component.cpp
//
// = DESCRIPTION
//    Visitors for generation of code for Component.
//
// = AUTHOR
//    Jeff Parsons
//
// ============================================================================

#include "ace/Log_Msg.h"

#include "idl_defines.h"
#include "utl_scope.h"
#include "utl_identifier.h"
#include "utl_exceptlist.h"
#include "nr_extern.h"
#include "ast_argument.h"
#include "ast_exception.h"

#include "be_component.h"
#include "be_provides.h"
#include "be_uses.h"
#include "be_publishes.h"
#include "be_emits.h"
#include "be_consumes.h"
#include "be_mirror_port.h"
#include "be_porttype.h"
#include "be_attribute.h"
#include "be_eventtype.h"
#include "be_typedef.h"
#include "be_operation.h"
#include "be_sequence.h"
#include "be_string.h"
#include "be_structure.h"
#include "be_typedef.h"
#include "be_valuetype.h"

#include "be_visitor_component.h"
#include "be_visitor_attribute.h"
#include "be_visitor_operation.h"
#include "be_visitor_interface.h"
#include "be_visitor_structure.h"
#include "be_visitor_typedef.h"
#include "be_visitor_typecode.h"
#include "be_visitor_context.h"
#include "be_util.h"
#include "be_helper.h"
#include "be_identifier_helper.h"
#include "be_extern.h"

#include "be_visitor_component/component.cpp"
#include "be_visitor_component/component_scope.cpp"
#include "be_visitor_component/component_ch.cpp"
#include "be_visitor_component/component_ci.cpp"
#include "be_visitor_component/component_cs.cpp"
#include "be_visitor_component/component_sh.cpp"
#include "be_visitor_component/component_si.cpp"
#include "be_visitor_component/component_ss.cpp"
#include "be_visitor_component/component_ih.cpp"
#include "be_visitor_component/component_is.cpp"
#include "be_visitor_component/component_svh.cpp"
#include "be_visitor_component/facet_svh.cpp"
#include "be_visitor_component/context_svh.cpp"
#include "be_visitor_component/servant_svh.cpp"
#include "be_visitor_component/component_svs.cpp"
#include "be_visitor_component/facet_svs.cpp"
#include "be_visitor_component/context_svs.cpp"
#include "be_visitor_component/servant_svs.cpp"
#include "be_visitor_component/component_ex_idl.cpp"
#include "be_visitor_component/facet_ex_idl.cpp"
#include "be_visitor_component/executor_ex_idl.cpp"
#include "be_visitor_component/context_ex_idl.cpp"
#include "be_visitor_component/component_exh.cpp"
#include "be_visitor_component/facet_exh.cpp"
#include "be_visitor_component/executor_exh.cpp"
#include "be_visitor_component/component_exs.cpp"
#include "be_visitor_component/facet_exs.cpp"
#include "be_visitor_component/executor_exs.cpp"
#include "be_visitor_component/any_op_ch.cpp"
#include "be_visitor_component/any_op_cs.cpp"
#include "be_visitor_component/cdr_op_ch.cpp"
#include "be_visitor_component/cdr_op_cs.cpp"

