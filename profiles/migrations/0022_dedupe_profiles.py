"""De-duplicate profile ownership ahead of the OneToOneField conversion.

Migration 0023 converts ``OrganizationProfile.owner`` and
``SpeakerProfile.user_account`` from ForeignKey to OneToOneField, which adds a
UNIQUE index. Any owner that holds more than one row would make that index
creation abort. This migration keeps the most recently updated profile per
owner and merges related rows onto the survivor before deleting the extras.

Child rows that live outside the profiles app (talks, feedbacks) are only
re-pointed when duplicates actually exist. A fresh database cannot contain
duplicate rows, so those tables may not yet exist when this migration runs.
"""

from django.db import migrations


def _rehome(apps, child_model, fk_field, loser, survivor):
    """Point a within-profiles child relation at the surviving profile."""
    model = apps.get_model("profiles", child_model)
    model.objects.filter(**{fk_field: loser}).update(**{fk_field: survivor})


def _dedupe_speaker_rows(apps, loser, survivor):
    """Merge a duplicate speaker profile's data onto the survivor."""
    SpeakerFollow = apps.get_model("profiles", "SpeakerFollow")

    for follow in SpeakerFollow.objects.filter(speaker=loser):
        if SpeakerFollow.objects.filter(
            follower=follow.follower, speaker=survivor
        ).exists():
            follow.delete()
        else:
            follow.speaker = survivor
            follow.save()

    _rehome(apps, "SpeakerSkillTag", "speaker", loser, survivor)
    _rehome(apps, "SpeakerExperiences", "speaker", loser, survivor)
    _rehome(apps, "SpeakerSocialLinks", "speaker", loser, survivor)

    for event in loser.events_spoken.all():
        survivor.events_spoken.add(event)

    Talks = apps.get_model("talks", "Talks")
    Talks.objects.filter(speaker=loser).update(speaker=survivor)

    Feedback = apps.get_model("feedbacks", "Feedback")
    Feedback.objects.filter(speaker=loser).update(speaker=survivor)

    EventFeedbackPreference = apps.get_model("feedbacks", "EventFeedbackPreference")
    for pref in EventFeedbackPreference.objects.filter(speaker=loser):
        if EventFeedbackPreference.objects.filter(
            speaker=survivor, event=pref.event
        ).exists():
            pref.delete()
        else:
            pref.speaker = survivor
            pref.save()

    loser.delete()


def dedupe_profiles(apps, schema_editor):
    """Keep one profile per owner, purging every duplicate set."""
    SpeakerProfile = apps.get_model("profiles", "SpeakerProfile")
    OrganizationProfile = apps.get_model("profiles", "OrganizationProfile")

    for owner_id in (
        OrganizationProfile.objects.filter(owner_id__isnull=False)
        .values_list("owner_id", flat=True)
        .distinct()
    ):
        owned = list(
            OrganizationProfile.objects.filter(owner_id=owner_id).order_by(
                "-updated_at", "-id"
            )
        )
        survivor, duplicates = owned[0], owned[1:]
        for duplicate in duplicates:
            duplicate.delete()

    for user_account_id in SpeakerProfile.objects.values_list(
        "user_account_id", flat=True
    ).distinct():
        owned = list(
            SpeakerProfile.objects.filter(user_account_id=user_account_id).order_by(
                "-updated_at", "-id"
            )
        )
        survivor, duplicates = owned[0], owned[1:]
        for duplicate in duplicates:
            _dedupe_speaker_rows(apps, loser=duplicate, survivor=survivor)


class Migration(migrations.Migration):
    """De-duplicate profile ownership before the unique constraints land."""

    dependencies = [
        ("profiles", "0021_alter_organizationprofile_cfps_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe_profiles, migrations.RunPython.noop),
    ]
