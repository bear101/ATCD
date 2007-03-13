// $Id$

#include "ace/Get_Opt.h"
#include "Big_Reply_i.h"
#include "ace/OS_NS_stdio.h"


ACE_RCSID(Big_Reply, server, "$Id$")

const char *ior_output_file = "test.ior";

// We can change this value if wanted..
const CORBA::ULong data_size = 4000000;

int
parse_args (int argc, char *argv[])
{
  ACE_Get_Opt get_opts (argc, argv, "o:s:");
  int c;

  while ((c = get_opts ()) != -1)
    switch (c)
      {
      case 'o':
        ior_output_file = get_opts.opt_arg ();
        break;
      case '?':
      default:
        ACE_ERROR_RETURN ((LM_ERROR,
                           "usage:  %s "
                           "-o <iorfile>"
                           "-i <no_iterations>"
                           "\n",
                           argv [0]),
                          -1);
      }
  // Indicates sucessful parsing of the command line
  return 0;
}

int
main (int argc, char *argv[])
{
  ACE_DEBUG ((LM_DEBUG, "Starting server\n"));

  try
    {
      CORBA::ORB_var orb =
        CORBA::ORB_init (argc, argv);

      CORBA::Object_var poa_object =
        orb->resolve_initial_references ("RootPOA");

      if (CORBA::is_nil (poa_object.in ()))
        ACE_ERROR_RETURN ((LM_ERROR,
                           " (%P|%t) Unable to initialize the POA.\n"),
                          1);

      PortableServer::POA_var root_poa =
        PortableServer::POA::_narrow (poa_object.in ());

      PortableServer::POAManager_var poa_manager =
        root_poa->the_POAManager ();


      if (parse_args (argc, argv) != 0)
        return 1;

      Big_Reply_i *big_reply_gen;

      ACE_NEW_RETURN (big_reply_gen,
                      Big_Reply_i (orb.in (),
                                   data_size),
                      1);


      PortableServer::ServantBase_var big_reply_owner_transfer(big_reply_gen);

      PortableServer::ObjectId_var id =
        root_poa->activate_object (big_reply_gen);

      CORBA::Object_var object = root_poa->id_to_reference (id.in ());

      Test::Big_Reply_var big_reply =
        Test::Big_Reply::_narrow (object.in ());

      CORBA::String_var ior =
        orb->object_to_string (big_reply.in ());

      // If the ior_output_file exists, output the ior to it
      FILE *output_file= ACE_OS::fopen (ior_output_file, "w");
      if (output_file == 0)
        ACE_ERROR_RETURN ((LM_ERROR,
                           "Cannot open output file for writing IOR: %s",
                           ior_output_file),
                              1);
      ACE_OS::fprintf (output_file, "%s", ior.in ());
      ACE_OS::fclose (output_file);

      poa_manager->activate ();

      orb->run ();
      ACE_DEBUG ((LM_DEBUG, "event loop finished\n"));

      root_poa->destroy (1, 1);
    }
  catch (const CORBA::Exception& ex)
    {
      ex._tao_print_exception ("Caught exception:");
      return 1;
    }

  ACE_DEBUG ((LM_DEBUG, "Ending server\n"));

  return 0;
}
