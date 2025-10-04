from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from emails.models import EmailTemplate
from emails.snapshot import render_html_to_snapshot_content

class Command(BaseCommand):
    help = "Generate/refresh snapshots for all EmailTemplate records."

    def add_arguments(self, parser):
        parser.add_argument("--refresh", action="store_true", help="Regenerate even if a snapshot exists")

    def handle(self, *args, **opts):
        refresh = opts["refresh"]
        qs = EmailTemplate.objects.all()
        count = qs.count()
        done = 0
        for tpl in qs:
            if refresh or not tpl.snapshot:
                content: ContentFile = render_html_to_snapshot_content(tpl.body_html or "")
                tpl.snapshot.save(f"template_{tpl.pk}.png", content, save=True)
                done += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {done}/{count} templates"))
