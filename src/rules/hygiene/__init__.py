# Copyright 2025 John Brosnihan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hygiene rules."""

from rules.hygiene.ci_rule import CiRule
from rules.hygiene.gitignore_rule import GitignoreRule
from rules.hygiene.forbidden_files_rule import ForbiddenFilesRule
from rules.hygiene.file_size_rule import FileSizeRule

__all__ = ["CiRule", "GitignoreRule", "ForbiddenFilesRule", "FileSizeRule"]
