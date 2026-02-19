#!/usr/bin/env python
"""
SkillSwap 数据填充脚本
生成大量测试数据用于界面测试

安全改造（方案 A）：
- 默认不创建管理员（避免固定密码 admin/admin123）
- 仅当设置 SEED_CREATE_ADMIN=1 时才创建管理员
  并且必须提供 SEED_ADMIN_PASSWORD（不会写死到代码里）
"""

import os
import sys
import random
from datetime import datetime, timedelta
from django.utils import timezone

# 设置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import IntegrityError  # noqa: E402
from skillswap.models import (  # noqa: E402
    Profile,
    Skill,
    UserSkill,
    Request,
    Match,
    Block,
    Feedback,
    Notification,
    Conversation,
    Message,
    Report,
)

User = get_user_model()

# =========================
# 可配置参数（可用环境变量覆盖）
# =========================
NUM_USERS = int(os.environ.get("SEED_NUM_USERS", "50"))
NUM_REQUESTS = int(os.environ.get("SEED_NUM_REQUESTS", "80"))
NUM_MATCHES = int(os.environ.get("SEED_NUM_MATCHES", "60"))
NUM_CONVERSATIONS = int(os.environ.get("SEED_NUM_CONVERSATIONS", "40"))

DEFAULT_USER_PASSWORD = os.environ.get("SEED_USER_PASSWORD", "testpass123")

# 技能数据
SKILL_CATEGORIES = {
    "programming": [
        "Python",
        "JavaScript",
        "Java",
        "C++",
        "Go",
        "Rust",
        "TypeScript",
        "React",
        "Vue.js",
        "Django",
        "Flask",
        "Node.js",
        "SQL",
        "MongoDB",
        "Docker",
        "Kubernetes",
    ],
    "language": [
        "English",
        "Spanish",
        "French",
        "German",
        "Japanese",
        "Korean",
        "Chinese",
        "Italian",
        "Portuguese",
        "Russian",
    ],
    "art": [
        "Photography",
        "Graphic Design",
        "UI/UX Design",
        "Illustration",
        "Video Editing",
        "3D Modeling",
        "Animation",
        "Painting",
        "Sketching",
    ],
    "music": [
        "Guitar",
        "Piano",
        "Violin",
        "Drums",
        "Singing",
        "Music Production",
        "DJing",
        "Music Theory",
        "Bass",
    ],
    "sports": [
        "Basketball",
        "Soccer",
        "Tennis",
        "Swimming",
        "Yoga",
        "Running",
        "Cycling",
        "Climbing",
        "Boxing",
        "Martial Arts",
    ],
    "other": [
        "Cooking",
        "Baking",
        "Gardening",
        "Chess",
        "Public Speaking",
        "Writing",
        "Marketing",
        "Finance",
        "Psychology",
        "First Aid",
    ],
}

# 名字数据
FIRST_NAMES = [
    "Emma",
    "Liam",
    "Olivia",
    "Noah",
    "Ava",
    "Ethan",
    "Sophia",
    "Mason",
    "Isabella",
    "William",
    "Mia",
    "James",
    "Charlotte",
    "Benjamin",
    "Amelia",
    "Lucas",
    "Harper",
    "Henry",
    "Evelyn",
    "Alexander",
    "Abigail",
    "Daniel",
    "Emily",
    "Matthew",
    "Elizabeth",
    "Jackson",
    "Sofia",
    "Sebastian",
    "Avery",
    "Jack",
    "Ella",
    "Owen",
    "Madison",
    "Samuel",
    "Scarlett",
    "David",
    "Victoria",
    "Joseph",
    "Chloe",
    "Carter",
    "Grace",
    "Wyatt",
    "Zoey",
    "John",
    "Nora",
    "Oliver",
    "Lily",
    "Gabriel",
    "Hannah",
    "Anthony",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
]

# 标题和描述模板
REQUEST_TITLES = [
    "Looking for a {skill} study partner",
    "Want to learn {skill} - beginner friendly",
    "Need help with {skill} project",
    "{skill} practice buddy wanted",
    "Teaching {skill} - join me!",
    "Looking for {skill} mentor",
    "{skill} exchange - I can teach you {my_skill}",
    "Group {skill} learning session",
    "{skill} crash course needed",
    "Advanced {skill} techniques",
]

REQUEST_DESCRIPTIONS = [
    "I'm a beginner looking to learn {skill}. Available weekday evenings and weekends.",
    "Have some experience with {skill} but want to improve. Prefer online sessions.",
    "Working on a project using {skill}. Need guidance from someone experienced.",
    "Looking for regular practice sessions for {skill}. Flexible schedule.",
    "Can teach {skill} at intermediate level. Looking for exchange opportunities.",
    "Want to master {skill} this semester. Serious learners only!",
    "Group study for {skill} - the more the merrier!",
    "Need quick help with {skill} basics before exam next week.",
    "Advanced learner seeking {skill} expert for challenging projects.",
    "Casual {skill} learning - fun and relaxed atmosphere preferred.",
]

BIO_TEMPLATES = [
    "Student passionate about {interest1} and {interest2}. Always eager to learn!",
    "Love {interest1} and looking to expand my skills in {interest2}.",
    "Experienced in {interest1}, now exploring {interest2}.",
    "Enthusiastic learner. Main interests: {interest1}, {interest2}.",
    "Campus explorer | {interest1} fan | {interest2} newbie",
    "Balancing studies with passion for {interest1} and {interest2}.",
    "Future expert in {interest1} and {interest2}. Let's learn together!",
    "Curious mind interested in {interest1} and {interest2}.",
]

AVAILABILITY_OPTIONS = [
    "Weekday mornings",
    "Weekday afternoons",
    "Weekday evenings",
    "Weekends only",
    "Flexible schedule",
    "Monday/Wednesday/Friday",
    "Tuesday/Thursday",
    "After 6pm weekdays",
    "Anytime on weekends",
    "Limited availability - message me",
]

PREFERRED_MODES = ["online", "offline", "both"]
SKILL_LEVELS = ["beginner", "intermediate", "advanced"]
SKILL_TYPES = ["offer", "want"]
MATCH_STATUSES = ["pending", "accepted", "rejected", "completed"]
NOTIFICATION_VERBS = ["invite_sent", "invite_accepted", "invite_rejected", "match_completed"]
REPORT_REASONS = ["spam", "harassment", "scam", "inappropriate", "other"]


def maybe_create_superuser(users):
    """
    可选创建超级用户（默认关闭）。

    触发条件：
    - SEED_CREATE_ADMIN=1
    - 必须提供 SEED_ADMIN_PASSWORD
    可选：
    - SEED_ADMIN_USERNAME（默认 admin）
    - SEED_ADMIN_EMAIL（默认 admin@skillswap.edu）
    """
    if os.environ.get("SEED_CREATE_ADMIN", "").strip() != "1":
        print("  ℹ️  Superuser creation disabled (set SEED_CREATE_ADMIN=1 to enable).")
        return

    admin_username = os.environ.get("SEED_ADMIN_USERNAME", "admin").strip() or "admin"
    admin_email = os.environ.get("SEED_ADMIN_EMAIL", "admin@skillswap.edu").strip() or "admin@skillswap.edu"
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD")

    if not admin_password:
        raise RuntimeError(
            "SEED_ADMIN_PASSWORD is required when SEED_CREATE_ADMIN=1. "
            "Either set it, or create an admin via `python manage.py createsuperuser`."
        )

    try:
        if User.objects.filter(username=admin_username).exists():
            admin = User.objects.get(username=admin_username)
            users.append(admin)
            print(f"  ℹ️  Superuser '{admin_username}' already exists, skipping creation.")
            return

        admin = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password,
        )
        users.append(admin)
        print(f"  ✅ Created superuser: {admin_username} (password not printed)")
    except IntegrityError:
        admin = User.objects.get(username=admin_username)
        users.append(admin)
        print(f"  ℹ️  Superuser '{admin_username}' already exists (IntegrityError), using existing.")


def create_users():
    """创建测试用户"""
    print("Creating users...")
    users = []

    # 方案 A：默认不创建超级用户（避免固定密码）
    maybe_create_superuser(users)

    # 创建普通用户
    for i in range(NUM_USERS):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"

        try:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@student.edu",
                password=DEFAULT_USER_PASSWORD,
                first_name=first_name,
                last_name=last_name,
            )

            # 更新 Profile
            profile = user.profile
            profile.bio = random.choice(BIO_TEMPLATES).format(
                interest1=random.choice(list(SKILL_CATEGORIES.keys())),
                interest2=random.choice(list(SKILL_CATEGORIES.keys())),
            )
            profile.availability = random.choice(AVAILABILITY_OPTIONS)
            profile.preferred_mode = random.choice(PREFERRED_MODES)
            profile.location = random.choice(["Campus Center", "Library", "Online", "Student Union", "Coffee Shop"])
            profile.save()

            users.append(user)

            if (i + 1) % 10 == 0:
                print(f"  Created {i + 1} users...")

        except IntegrityError:
            continue

    print(f"Total users created/loaded: {len(users)}")
    return users


def create_skills():
    """创建技能"""
    print("\nCreating skills...")
    skills = []

    for category, skill_names in SKILL_CATEGORIES.items():
        for name in skill_names:
            skill, created = Skill.objects.get_or_create(
                name=name,
                category=category,
                defaults={"description": f"Learn {name} with fellow students"},
            )
            skills.append(skill)
            if created:
                print(f"  Created skill: {name} ({category})")

    print(f"Total skills: {len(skills)}")
    return skills


def create_user_skills(users, skills):
    """为用户分配技能"""
    print("\nAssigning skills to users...")
    count = 0

    for user in users:
        # 每个用户拥有 2-6 个技能
        num_skills = random.randint(2, 6)
        user_skills = random.sample(skills, min(num_skills, len(skills)))

        for skill in user_skills:
            skill_type = random.choice(SKILL_TYPES)
            level = random.choice(SKILL_LEVELS)

            try:
                UserSkill.objects.create(
                    user=user,
                    skill=skill,
                    type=skill_type,
                    level=level,
                    learning_months=random.randint(1, 36) if level != "beginner" else random.randint(0, 6),
                    self_rating=random.randint(1, 5) if level != "beginner" else random.randint(1, 3),
                )
                count += 1
            except IntegrityError:
                continue

        if count % 50 == 0 and count > 0:
            print(f"  Assigned {count} user skills...")

    print(f"Total user skills: {count}")


def create_requests(users, skills):
    """创建学习请求"""
    print("\nCreating learning requests...")
    requests_list = []

    for i in range(NUM_REQUESTS):
        user = random.choice(users)
        skill = random.choice(skills)

        title_template = random.choice(REQUEST_TITLES)
        # 获取用户的 offer 技能用于交换
        user_offers = UserSkill.objects.filter(user=user, type="offer")
        my_skill = user_offers.first().skill.name if user_offers.exists() else "something interesting"

        title = title_template.format(skill=skill.name, my_skill=my_skill)
        description = random.choice(REQUEST_DESCRIPTIONS).format(skill=skill.name)

        req = Request.objects.create(
            user=user,
            skill=skill,
            title=title,
            description=description,
            status="open",
            preferred_time=random.choice(AVAILABILITY_OPTIONS),
        )
        requests_list.append(req)

        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1} requests...")

    print(f"Total requests: {len(requests_list)}")
    return requests_list


def create_matches(users, requests_list):
    """创建匹配"""
    print("\nCreating matches...")
    matches = []

    open_requests = [r for r in requests_list if r.status == "open"]

    for i in range(min(NUM_MATCHES, len(open_requests))):
        req = random.choice(open_requests)
        # 找到不是请求创建者的用户
        potential_partners = [u for u in users if u != req.user]
        if not potential_partners:
            continue

        partner = random.choice(potential_partners)

        # 随机状态，但 pending 和 accepted 居多
        status_weights = ["pending"] * 4 + ["accepted"] * 3 + ["rejected"] * 2 + ["completed"] * 1
        status = random.choice(status_weights)

        try:
            match = Match.objects.create(
                request=req,
                requester=partner,  # 发起者
                partner=req.user,  # request 创建者
                status=status,
            )
            matches.append(match)

            # 如果匹配完成，关闭请求
            if status == "completed":
                req.status = "closed"
                req.save()

            # 创建通知
            if status == "pending":
                Notification.objects.create(
                    user=req.user,
                    actor=partner,
                    match=match,
                    verb="invite_sent",
                    message=f'{partner.username} sent you a match invite for "{req.title}"',
                )

            if (i + 1) % 15 == 0:
                print(f"  Created {i + 1} matches...")

        except IntegrityError:
            continue

    print(f"Total matches: {len(matches)}")
    return matches


def create_conversations_and_messages(matches):
    """创建对话和消息"""
    print("\nCreating conversations and messages...")

    accepted_matches = [m for m in matches if m.status in ["accepted", "completed"]]

    for i, match in enumerate(accepted_matches[:NUM_CONVERSATIONS]):
        # 创建对话
        conversation, created = Conversation.objects.get_or_create(match=match)

        if not created:
            continue

        # 创建消息
        num_messages = random.randint(3, 8)
        participants = [match.requester, match.partner]

        for _ in range(num_messages):
            sender = random.choice(participants)
            body = random.choice(
                [
                    "Hey! I'm interested in learning together.",
                    "When are you usually free?",
                    "I can meet on campus or online, whatever works for you!",
                    "That sounds great! I'm available next week.",
                    "Should we meet at the library?",
                    "Thanks for accepting my invite!",
                    "Looking forward to our session.",
                    "I have some materials I can share with you.",
                    "Perfect! See you then.",
                    "Let me know if you need to reschedule.",
                ]
            )

            Message.objects.create(
                conversation=conversation,
                sender=sender,
                body=body,
                is_read=random.choice([True, True, True, False]),  # 大部分已读
            )

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} conversations...")

    total_messages = Message.objects.count()
    print(f"Total messages: {total_messages}")


def create_blocks(users):
    """创建屏蔽关系"""
    print("\nCreating block relationships...")
    count = 0

    for _ in range(20):  # 创建 20 个屏蔽关系
        blocker = random.choice(users)
        blocked = random.choice([u for u in users if u != blocker])

        try:
            Block.objects.get_or_create(blocker=blocker, blocked=blocked)
            count += 1
        except IntegrityError:
            continue

    print(f"Total blocks: {count}")


def create_feedback(matches):
    """创建评价"""
    print("\nCreating feedback...")
    count = 0

    completed_matches = [m for m in matches if m.status == "completed"]

    for match in completed_matches[:30]:  # 为 30 个完成的匹配创建评价
        participants = [match.requester, match.partner]

        for rater in participants:
            ratee = match.partner if rater == match.requester else match.requester

            comments = random.choice(
                [
                    "Great learning experience!",
                    "Very helpful and patient.",
                    "Knowledgeable and friendly.",
                    "Good communication skills.",
                    "Highly recommended!",
                    "Learned a lot from this session.",
                    "Professional and punctual.",
                    "Would love to learn together again.",
                ]
            )

            try:
                Feedback.objects.create(
                    match=match,
                    rater=rater,
                    ratee=ratee,
                    rating=random.randint(3, 5),
                    comment=comments,
                )
                count += 1
            except IntegrityError:
                continue

    print(f"Total feedback entries: {count}")


def create_bookmarks(users, requests_list):
    """创建书签"""
    print("\nCreating bookmarks...")
    count = 0

    for user in users[:30]:  # 前 30 个用户创建书签
        num_bookmarks = random.randint(0, 5)
        bookmarked_requests = random.sample(requests_list, min(num_bookmarks, len(requests_list)))

        for req in bookmarked_requests:
            if req.user != user:  # 不收藏自己的
                user.profile.bookmarked_requests.add(req)
                count += 1

    print(f"Total bookmarks: {count}")


def create_reports(users, requests_list):
    """创建举报（少量）"""
    print("\nCreating reports...")

    for _ in range(5):  # 只创建 5 个举报
        reporter = random.choice(users)
        reported_user = random.choice([u for u in users if u != reporter])
        req = random.choice(requests_list)

        Report.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            content_object=req,
            reason=random.choice(REPORT_REASONS),
            details="This is a test report for moderation testing.",
        )

    print("Total reports: 5")


def print_summary():
    """打印数据摘要"""
    print("\n" + "=" * 50)
    print("DATA SEEDING COMPLETE!")
    print("=" * 50)
    print(f"Users: {User.objects.count()}")
    print(f"Skills: {Skill.objects.count()}")
    print(f"User Skills: {UserSkill.objects.count()}")
    print(f"Requests: {Request.objects.count()}")
    print(f"Matches: {Match.objects.count()}")
    print(f"Conversations: {Conversation.objects.count()}")
    print(f"Messages: {Message.objects.count()}")
    print(f"Blocks: {Block.objects.count()}")
    print(f"Feedback: {Feedback.objects.count()}")
    print(f"Notifications: {Notification.objects.count()}")
    print(f"Reports: {Report.objects.count()}")
    print("=" * 50)

    # 不打印管理员固定口令（避免安全风险）
    print("\nLogin notes:")
    print(f"  - Regular users password: {DEFAULT_USER_PASSWORD} (set via SEED_USER_PASSWORD)")
    print("  - Superuser is NOT created by default.")
    print("    Create one safely via:")
    print("      python manage.py createsuperuser")
    print("    Or (optional) enable scripted creation via env vars:")
    print("      SEED_CREATE_ADMIN=1 SEED_ADMIN_PASSWORD='your-strong-password' python seed_data.py")


def main():
    """主函数"""
    print("=" * 50)
    print("SkillSwap Data Seeding Script")
    print("=" * 50)

    users = create_users()
    skills = create_skills()
    create_user_skills(users, skills)
    requests_list = create_requests(users, skills)
    matches = create_matches(users, requests_list)
    create_conversations_and_messages(matches)
    create_blocks(users)
    create_feedback(matches)
    create_bookmarks(users, requests_list)
    create_reports(users, requests_list)

    print_summary()


if __name__ == "__main__":
    main()