# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implements command to update an ops agents policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.instances.ops_agents import cloud_ops_agents_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents import cloud_ops_agents_util
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import cloud_ops_agents_policy_to_os_assignment_policy_converter as to_os_policy_assignment
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import guest_policy_to_ops_agents_policy_converter
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import ops_agents_policy_to_guest_policy_converter
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import os_policy_assignment_to_cloud_ops_agents_policy_converter as to_ops_agents_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import cloud_ops_agents_policy_validator
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import ops_agents_policy_validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances.ops_agents.policies import parser_utils
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.osconfig.v1 import osconfig_v1_messages as osconfig


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateAlphaBeta(base.Command):
  """Update a Google Cloud operations suite agent (Ops Agent) policy.

  *{command}* updates a policy that facilitates agent management across
  Compute Engine instances based on user specified instance filters. This policy
  installs, specifies versioning, enables autoupgrade, and removes Ops Agents.

  The command returns the content of the updated policy or an error indicating
  why the update fails. The updated policy takes effect asynchronously. It
  can take 10-15 minutes for the VMs to enforce the updated policy.

  The available flags for the ``update'' command are similar to the flags for
  the ``create'' command. All the flags for ``update'' are optional. If a flag
  is not specified, it retains the original value. The full value of each flag
  needs to be re-stated during ``update''. Take the ``--agents'' flag for
  example:

  If the original policy specified two agents
  (``--agents="type=logging;type=metrics"''), and only one agent
  (``--agents="type=logging"'') is specified in a *{command}* command, then the
  policy stops managing and enforcing the unspecified agent. In order to remove
  the metrics agent in this case, set the package state explicitly to
  ``removed'' (``--agents="type=logging;type=metrics,package-state=removed"'').

  In order to explicitly clear the ``--group-labels'', ``--instances'', and
  ``--zones'' instance filters, use the following flags as documented below:
  ``--clear-group-labels'', ``--clear-instances'', and ``--clear-zones'' flags.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To update a policy named ``ops-agents-test-policy'' to target a
          single CentOS 7 VM instance named
          ``zones/us-central1-a/instances/test-instance'' for testing or
          development, and install both Logging and Monitoring Agents on that
          VM instance, run:

          $ {command} ops-agents-test-policy --agent-rules="type=logging,enable-autoupgrade=false;type=metrics,enable-autoupgrade=false" --instances=zones/us-central1-a/instances/test-instance --os-types=short-name=centos,version=7

          To update a policy named ``ops-agents-prod-policy'' to target all
          CentOS 7 VMs in zone ``us-central1-a'' with either
          ``env=prod,product=myapp'' labels or ``env=staging,product=myapp''
          labels, and make sure the logging agent and metrics agent versions are
          pinned to specific major versions for staging and production, run:

          $ {command} ops-agents-prod-policy --agent-rules="type=logging,version=1.*.*,enable-autoupgrade=false;type=metrics,version=6.*.*,enable-autoupgrade=false" --group-labels="env=prod,product=myapp;env=staging,product=myapp" --os-types=short-name=centos,version=7 --zones=us-central1-a

          To update a policy named ``ops-agents-labels-policy'' to clear the
          instances filters and use a group labels filter instead to target VMs
          with either ``env=prod,product=myapp'' or
          ``env=staging,product=myapp'' labels, run:

          $ {command} ops-agents-labels-policy --clear-instances --group-labels="env=prod,product=myapp;env=staging,product=myapp"

          To perform the same update as above, conditionally on the fact that
          the policy's etag (retrieved by an earlier command) is
          ``f59741c8-bb5e-4ee6-bf6f-c4ebeb6b06e0'', run:

          $ {command} ops-agents-labels-policy --clear-instances --group-labels="env=prod,product=myapp;env=staging,product=myapp" --etag=f59741c8-bb5e-4ee6-bf6f-c4ebeb6b06e0
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser_utils.AddSharedArgs(parser)
    parser_utils.AddMutationArgs(parser=parser, required=False)
    parser_utils.AddUpdateArgs(parser)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(
        release_track, api_version_override='v1beta'
    )
    messages = osconfig_api_utils.GetClientMessages(
        release_track, api_version_override='v1beta'
    )

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsGuestPoliciesGetRequest(
        name=osconfig_command_utils.GetGuestPolicyUriPath(
            'projects', project, args.POLICY_ID
        )
    )
    service = client.projects_guestPolicies
    current_guest_policy = service.Get(request)
    current_ops_agents_policy = guest_policy_to_ops_agents_policy_converter.ConvertGuestPolicyToOpsAgentPolicy(
        current_guest_policy
    )
    updated_ops_agents_policy = ops_agents_policy.UpdateOpsAgentsPolicy(
        current_ops_agents_policy,
        args.description,
        args.etag,
        args.agent_rules,
        args.os_types,
        [] if args.clear_group_labels else args.group_labels,
        [] if args.clear_zones else args.zones,
        [] if args.clear_instances else args.instances,
    )
    ops_agents_policy_validator.ValidateOpsAgentsPolicy(
        updated_ops_agents_policy
    )
    updated_os_config_policy = ops_agents_policy_to_guest_policy_converter.ConvertOpsAgentPolicyToGuestPolicy(
        messages, updated_ops_agents_policy, current_guest_policy.recipes
    )
    request = messages.OsconfigProjectsGuestPoliciesPatchRequest(
        guestPolicy=updated_os_config_policy,
        name=osconfig_command_utils.GetGuestPolicyUriPath(
            'projects', project, args.POLICY_ID
        ),
        updateMask=None,
    )
    complete_os_config_policy = service.Patch(request)
    complete_ops_agent_policy = guest_policy_to_ops_agents_policy_converter.ConvertGuestPolicyToOpsAgentPolicy(
        complete_os_config_policy
    )
    return complete_ops_agent_policy


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Google Cloud operations suite agent (Ops Agent) policy.

  TBD
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          TBD
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser.add_argument(
        'POLICY_ID',
        type=str,
        help="""\
          ID of the policy.

          This ID must contain only lowercase letters,
          numbers, and hyphens, end with a number or a letter, be between 1-63
          characters, and be unique within the project.
          """,
    )
    parser.add_argument(
        '--file',
        required=True,
        help="""\
          YAML file with a subset of Cloud Ops Policy fields you wish to update. For
          information about the Cloud Ops Agents Policy Assignment format, see [PLACEHOLDER for our public doc].""",
    )
    parser.add_argument(
        '--zone',
        required=True,
        help="""\
          Zone where the OS Policy Assignment is located.""",
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=(
            'If provided, the resulting OSPolicyAssignment will be printed to'
            ' standard output and no actual changes are made.'
        ),
    )

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    project = properties.VALUES.core.project.GetOrFail()
    # Make sure the policy we're updating is a valid Ops Agents policy.
    current_ops_agents_policy = cloud_ops_agents_util.GetOpsAgentsPolicyFromApi(
        release_track, args.POLICY_ID, project, args.zone
    )

    # Grab user's config.
    config = yaml.load_path(args.file)

    updated_policy = cloud_ops_agents_policy.UpdateOpsAgentsPolicy(
        update_ops_agents_policy=config,
        ops_agents_policy=current_ops_agents_policy,
    )
    cloud_ops_agents_policy_validator.ValidateOpsAgentsPolicy(updated_policy)

    if args.dry_run:
      return updated_policy

    parent_path = osconfig_command_utils.GetProjectLocationUriPath(
        project, args.zone
    )
    assignment_id = osconfig_command_utils.GetOsPolicyAssignmentRelativePath(
        parent_path, args.POLICY_ID
    )
    messages = osconfig_api_utils.GetClientMessages(release_track)

    # TODO: b/339694475 - Include updateMask to better indicate what fields
    # were updated.
    update_request = messages.OsconfigProjectsLocationsOsPolicyAssignmentsPatchRequest(
        oSPolicyAssignment=to_os_policy_assignment.ConvertOpsAgentsPolicyToOSPolicyAssignment(
            name=assignment_id, ops_agents_policy=updated_policy
        ),
        name=assignment_id,
    )

    client = osconfig_api_utils.GetClientInstance(release_track)
    service = client.projects_locations_osPolicyAssignments
    update_reponse = service.Patch(update_request)

    # Converting osconfig.Operation.ReponseValue to osconfig.OSPolicyAssignment.
    updated_os_policy_assignment = encoding.PyValueToMessage(
        osconfig.OSPolicyAssignment,
        encoding.MessageToPyValue(update_reponse.response),
    )

    updated_ops_agents_policy = (
        to_ops_agents_policy.ConvertOsPolicyAssignmentToCloudOpsAgentPolicy(
            updated_os_policy_assignment
        )
    )

    assert updated_ops_agents_policy == updated_policy

    return updated_policy.ToPyValue()
