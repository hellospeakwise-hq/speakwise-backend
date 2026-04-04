import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from organizations.models import Organization, OrganizationMembership
from events.models import Tag, Country, Location, Event
from attendees.models import AttendeeProfile, Attendance
from speakers.models import SpeakerProfile, SpeakerSkillTag, SpeakerExperiences, SpeakerSocialLinks, SpeakerFollow
from talks.models import Talks, Session, TalkReviewComment
from feedbacks.models import Feedback
from teams.models import TeamMember, TeamSocial
from speakerrequests.models import SpeakerRequest
from organizations.choices import OrganizationRole
from talks.choices import TalkCategoryChoices

class Command(BaseCommand):
    help = "Seed the database with sample data for all models."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        # 1. Users
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                password="password123",
                first_name=f"First_{i}",
                last_name=f"Last_{i}",
                nationality=random.choice(["US", "UK", "KE", "NG", "DE", "FR"])
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users"))

        # 2. Organizations
        orgs = []
        for i in range(3):
            org = Organization.objects.create(
                name=f"Org {i}",
                description=f"Description for Org {i}",
                email=f"org{i}@example.com",
                website=f"https://org{i}.com",
                is_active=True,
                status="approved",
                created_by=random.choice(users),
                slug=f"org-{i}"
            )
            orgs.append(org)
            
            # Organization Memberships
            for user in random.sample(users, 3):
                OrganizationMembership.objects.create(
                    organization=org,
                    user=user,
                    role=random.choice(OrganizationRole.values),
                    is_active=True,
                    added_by=random.choice(users)
                )
        self.stdout.write(self.style.SUCCESS(f"Created {len(orgs)} organizations and memberships"))

        # 3. Tags & Countries
        tags = []
        tag_names = ["Python", "Django", "AI", "DevOps", "Web", "Cloud"]
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name, color=random.choice(["#ff0000", "#00ff00", "#0000ff", "#ffff00"]))
            tags.append(tag)
        
        countries = []
        country_data = [("Kenya", "KE"), ("Nigeria", "NG"), ("United States", "US"), ("United Kingdom", "UK")]
        for name, code in country_data:
            country, _ = Country.objects.get_or_create(name=name, code=code)
            countries.append(country)
        self.stdout.write(self.style.SUCCESS(f"Created {len(tags)} tags and {len(countries)} countries"))

        # 4. Locations
        locations = []
        for i in range(5):
            loc = Location.objects.create(
                venue=f"Venue {i}",
                address=f"{i} Main St",
                city="Nairobi",
                country=random.choice(countries)
            )
            locations.append(loc)
        self.stdout.write(self.style.SUCCESS(f"Created {len(locations)} locations"))

        # 5. Events
        events = []
        for i in range(5):
            event = Event.objects.create(
                title=f"Event {i}",
                short_description=f"Short desc {i}",
                description=f"Long description for event {i}",
                location=random.choice(locations),
                start_date_time=timezone.now() + timezone.timedelta(days=i),
                end_date_time=timezone.now() + timezone.timedelta(days=i, hours=2),
                is_active=True,
                organizer=random.choice(orgs)
            )
            event.tags.set(random.sample(tags, 2))
            events.append(event)
        self.stdout.write(self.style.SUCCESS(f"Created {len(events)} events"))

        # 6. Attendee Profiles & Attendance
        for user in users[:5]:
            profile = AttendeeProfile.objects.create(
                user_account=user,
                notification_preference="email",
                organization="Tech Co",
                is_verified=True
            )
            for event in random.sample(events, 2):
                Attendance.objects.create(
                    event=event,
                    email=user.email,
                    username=user.username,
                    is_verified=True
                )
        self.stdout.write(self.style.SUCCESS("Created attendee profiles and attendance"))

        # 7. Speaker Profiles & Related Data
        speakers = []
        for user in users[5:]:
            speaker = SpeakerProfile.objects.create(
                user_account=user,
                organization="Speaker Org",
                short_bio="I am a speaker",
                long_bio="Detailed bio here",
                country="Kenya"
            )
            speaker.events_spoken.set(random.sample(events, 2))
            speakers.append(speaker)

            # Skill Tags
            SpeakerSkillTag.objects.create(
                name="Public Speaking",
                duration=random.randint(1, 10),
                speaker=speaker
            )

            # Experiences
            SpeakerExperiences.objects.create(
                event_name="Past Event",
                event_date=timezone.now().date() - timezone.timedelta(days=30),
                topic="How to Speak",
                speaker=speaker
            )

            # Social Links
            SpeakerSocialLinks.objects.create(
                speaker=speaker,
                name="Twitter",
                url=f"https://twitter.com/{user.username}"
            )
            
            # Follows
            for follower in random.sample(users[:5], 2):
                SpeakerFollow.objects.create(
                    follower=follower,
                    speaker=speaker
                )
        self.stdout.write(self.style.SUCCESS(f"Created {len(speakers)} speaker profiles and related data"))

        # 8. Talks & Sessions
        talks_list = []
        for speaker in speakers:
            talk = Talks.objects.create(
                title=f"Talk by {speaker.user_account.username}",
                description="Amazing talk description",
                speaker=speaker,
                duration=45,
                category=random.choice(TalkCategoryChoices.values),
                is_public=True,
                event=random.choice(events)
            )
            talks_list.append(talk)

            # Sessions
            Session.objects.create(
                type="Main Hall",
                duration=45,
                talk=talk
            )

            # Review Comments
            TalkReviewComment.objects.create(
                talk=talk,
                rating=random.randint(1, 5),
                comment="Great talk!"
            )
        self.stdout.write(self.style.SUCCESS(f"Created {len(talks_list)} talks and sessions"))

        # 9. Feedbacks
        for speaker in random.sample(speakers, 2):
            Feedback.objects.create(
                speaker=speaker,
                overall_rating=8,
                engagement=9,
                clarity=8,
                content_depth=7,
                speaker_knowledge=9,
                practical_relevance=8,
                comments="Really enjoyed it"
            )
        self.stdout.write(self.style.SUCCESS("Created feedbacks"))

        # 10. Team Members
        for i in range(3):
            team_member = TeamMember.objects.create(
                name=f"Team Member {i}",
                role="Developer",
                short_bio="Helping build SpeakWise",
                display_order=i
            )
            TeamSocial.objects.create(
                team_member=team_member,
                name="LinkedIn",
                url=f"https://linkedin.com/member{i}"
            )
        self.stdout.write(self.style.SUCCESS("Created team members"))

        # 11. Speaker Requests
        for speaker in speakers[:2]:
            SpeakerRequest.objects.create(
                organizer=random.choice(orgs),
                speaker=speaker,
                event=random.choice(events),
                status="pending",
                message="Please speak at our event"
            )
        self.stdout.write(self.style.SUCCESS("Created speaker requests"))

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
