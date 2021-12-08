# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import textwrap
from pathlib import Path

import yaml

from craft_parts import LifecycleManager, Step


def test_dotnet_plugin(new_dir):
    parts_yaml = textwrap.dedent(
        """
        parts:
          foo:
            source: .
            plugin: dotnet
            dotnet-self-contained-runtime-identifier: linux-x64
            build-environment:
              - PATH: $TEST_DOTNET_STAGE/sdk:$PATH
            after: [dotnet]
          dotnet:
            plugin: dump
            source: https://download.visualstudio.microsoft.com/download/pr/17b6759f-1af0-41bc-ab12-209ba0377779/e8d02195dbf1434b940e0f05ae086453/dotnet-sdk-6.0.100-linux-x64.tar.gz
            source-checksum: sha256/8489a798fcd904a32411d64636e2747edf108192e0b65c6c3ccfb0d302da5ecb
            override-build: |
              # TODO: find out why this is a problem with "organize".XS
              cp --archive --link --no-dereference . $TEST_DOTNET_PART_INSTALL/sdk
            prime:
              - -sdk
        """
    )
    parts = yaml.safe_load(parts_yaml)

    Path("dotnet.csproj").write_text(
        textwrap.dedent(
            """
            <Project Sdk="Microsoft.NET.Sdk">

              <PropertyGroup>
                <OutputType>Exe</OutputType>
                <TargetFramework>net6.0</TargetFramework>
                <ImplicitUsings>enable</ImplicitUsings>
                <Nullable>enable</Nullable>
                <RuntimeIdentifier>linux-x64</RuntimeIdentifier>
              </PropertyGroup>

            </Project>
            """
        )
    )

    Path("hello.cs").write_text('Console.WriteLine("Hello, World!");')

    lf = LifecycleManager(parts, application_name="test_dotnet", cache_dir=new_dir)
    actions = lf.plan(Step.PRIME)

    with lf.action_executor() as ctx:
        ctx.execute(actions)

    binary = Path(lf.project_info.prime_dir, "dotnet")

    output = subprocess.check_output([str(binary)], text=True)
    assert output == "Hello, World!\n"