#!/usr/bin/env python3
"""Rebuild ~/germline/effectors/DueAddRecurring.shortcut from scratch.

Run when the shortcut needs to be updated or re-signed.
Usage: python3 ~/germline/effectors/build-due-shortcut.py
Then: open ~/germline/effectors/DueAddRecurring.shortcut → click "Add Shortcut"
"""

import os
import plistlib
import subprocess
import tempfile
import uuid


def u():
    return str(uuid.uuid4()).upper()


uid_gettext = u()
uid_split = u()
uid_title = u()
uid_datestr = u()
uid_date = u()
uid_action = u()

# Shortcut: accepts "title|ISO_date" as text input, creates weekly recurring reminder in Due
# Input format: "Meeting title|2026-03-11T11:25:00+0800"
plist = {
    "WFWorkflowName": "Due Add Recurring",
    "WFWorkflowClientVersion": "2600.0.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowHasInputFallback": False,
    "WFWorkflowInputContentItemClasses": ["WFStringContentItem"],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowTypes": [],
    "WFWorkflowImportQuestions": [],
    "WFWorkflowIcon": {
        "WFWorkflowIconGlyphNumber": 59511,
        "WFWorkflowIconStartColor": 4274264319,
    },
    "WFWorkflowActions": [
        # 1. Receive input as text
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
            "WFWorkflowActionParameters": {
                "UUID": uid_gettext,
                "WFTextActionText": {
                    "Value": {
                        "attachmentsByRange": {"{0, 1}": {"Type": "ExtensionInput"}},
                        "string": "\ufffc",
                    },
                    "WFSerializationType": "WFTextTokenString",
                },
            },
        },
        # 2. Split by | (macOS 26: is.workflow.actions.text.split, input key: 'text')
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.text.split",
            "WFWorkflowActionParameters": {
                "UUID": uid_split,
                "text": {
                    "Value": {
                        "OutputName": "Text",
                        "OutputUUID": uid_gettext,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "WFTextSeparator": "Custom",
                "WFTextCustomSeparator": "|",
            },
        },
        # 3. Get item 1 (title)
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
            "WFWorkflowActionParameters": {
                "UUID": uid_title,
                "WFInput": {
                    "Value": {
                        "OutputName": "Split Text",
                        "OutputUUID": uid_split,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "WFItemIndex": 1,
            },
        },
        # 4. Get item 2 (date ISO string)
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getitemfromlist",
            "WFWorkflowActionParameters": {
                "UUID": uid_datestr,
                "WFInput": {
                    "Value": {
                        "OutputName": "Split Text",
                        "OutputUUID": uid_split,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "WFItemIndex": 2,
            },
        },
        # 5. Detect date from ISO string
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.detect.date",
            "WFWorkflowActionParameters": {
                "UUID": uid_date,
                "WFInput": {
                    "Value": {
                        "OutputName": "Item from List",
                        "OutputUUID": uid_datestr,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
            },
        },
        # 6. Create recurring reminder in Due (bundle-prefixed identifier required)
        {
            "WFWorkflowActionIdentifier": "com.phocusllp.duemac.CreateRepeatingReminderIntent",
            "WFWorkflowActionParameters": {
                "UUID": uid_action,
                "title": {
                    "Value": {
                        "OutputName": "Item from List",
                        "OutputUUID": uid_title,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "date": {
                    "Value": {
                        "OutputName": "Dates",
                        "OutputUUID": uid_date,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "repeatFrequency": {"identifier": "week", "value": 1},
                "repeatIntervalWeekly": 1,
                "syncWhenRun": True,
            },
        },
    ],
}

# Build and sign
with tempfile.NamedTemporaryFile(suffix=".shortcut", delete=False) as f:
    tmp_unsigned = f.name

tmp_signed = os.path.expanduser("~/germline/effectors/DueAddRecurring.shortcut")

plist_data = plistlib.dumps(plist, fmt=plistlib.FMT_BINARY)
with open(tmp_unsigned, "wb") as f:
    f.write(plist_data)

result = subprocess.run(
    ["shortcuts", "sign", "--mode", "anyone", "--input", tmp_unsigned, "--output", tmp_signed],
    capture_output=True,
    text=True,
)
os.unlink(tmp_unsigned)

if result.returncode == 0:
    print(f"Built: {tmp_signed}")
    print(
        'Next: open ~/germline/effectors/DueAddRecurring.shortcut → click "Add Shortcut" in Shortcuts.app'
    )
    print('Imports as "DueAddRecurring" — moneo --sync will use this shortcut.')
else:
    print(f"Sign failed: {result.stderr}")
