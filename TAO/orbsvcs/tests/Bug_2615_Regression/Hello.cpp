//
// $Id: Hello.cpp,v 1.1 2006/07/26 12:54:06 sm Exp $
//

#include "ServerRequest_Interceptor2.h"
#include "Hello.h"

ACE_RCSID(Hello, Hello, "$Id: Hello.cpp,v 1.1 2006/07/26 12:54:06 sm Exp $")

Hello::Hello (CORBA::ORB_ptr orb, Test::Hello_ptr, CORBA::ULong)
  : orb_ (CORBA::ORB::_duplicate (orb))
{
}

void
Hello::shutdown (ACE_ENV_SINGLE_ARG_DECL)
  ACE_THROW_SPEC ((CORBA::SystemException))
{
  this->orb_->shutdown (0 ACE_ENV_ARG_PARAMETER);
}

void
Hello::ping (ACE_ENV_SINGLE_ARG_DECL)
  ACE_THROW_SPEC ((CORBA::SystemException))
{
  return;
}

CORBA::Boolean
Hello::has_ft_request_service_context (ACE_ENV_SINGLE_ARG_DECL)
  ACE_THROW_SPEC ((CORBA::SystemException))
{
  return ServerRequest_Interceptor2::has_ft_request_sc_;
}
