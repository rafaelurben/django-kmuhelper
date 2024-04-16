import abc

from django.contrib import messages
from django.utils.translation import ngettext
from kmuhelper import settings
from rich import print
from rich.progress import Progress
from woocommerce import API as WCAPI


def create_wc_api_object():
    """Create a API object from data stored in settings"""
    return WCAPI(
        url=settings.get_secret_db_setting("wc-url"),
        consumer_key=settings.get_secret_db_setting("wc-consumer_key"),
        consumer_secret=settings.get_secret_db_setting("wc-consumer_secret"),
    )


class WC_BaseAPI(abc.ABC):
    def __init__(self, wcapi: WCAPI = None):
        self.wcapi = wcapi or create_wc_api_object()

    # Logging

    LOG_PREFIX = NotImplemented

    def log(self, string, *args):
        print(self.LOG_PREFIX, string, *args)


class WC_BaseObjectAPI(WC_BaseAPI, abc.ABC):
    """Base CRUD class for WC API"""

    MODEL = NotImplemented
    WC_OBJ_DOES_NOT_EXIST_CODE = NotImplemented
    WC_API_BASEURL = NotImplemented

    # Object methods

    @abc.abstractmethod
    def create_object_from_data(self, wc_obj: dict):
        """Create a new object from WooCommerce data

        Must be implemented in subclass.

        Returns: The created database object
        """

        raise NotImplementedError()

    @abc.abstractmethod
    def update_object_from_data(self, db_obj, wc_obj: dict):
        """Update an existing object with WooCommerce data

        Must be implemented in subclass.

        Returns: nothing"""

        raise NotImplementedError()

    def delete_object_from_data(self, db_obj, wc_obj: dict):
        """Mark an existing object as deleted

        Should be overridden by subclasses if there are dependencies that need to be removed.

        Returns: nothing"""

        db_obj.woocommerce_deleted = True
        db_obj.save()

    def update_object_from_api(self, db_object) -> bool:
        """Update a specific product from WooCommerce"""

        response = self.wcapi.get(f"{self.WC_API_BASEURL}/{db_object.woocommerceid}")
        wc_obj = response.json()

        if response.status_code != 200:
            self.log(
                "[red]Object update failed with status code {}".format(
                    response.status_code
                )
            )
            if "code" in wc_obj and wc_obj["code"] == self.WC_OBJ_DOES_NOT_EXIST_CODE:
                self.log(
                    "[red]Object does not exist in WooCommerce![/] Link removed.",
                    str(db_object),
                )
                db_object.woocommerceid = 0
                db_object.woocommerce_deleted = True
                db_object.save()
            else:
                self.log(wc_obj)
            return False

        try:
            self.update_object_from_data(db_object, wc_obj)
        except Exception as e:
            self.log("[red]Object update failed with exception {}".format(e))
            return False
        return True

    def bulk_update_objects_from_api(
        self, db_queryset, request=None
    ) -> (int, int, int):
        """Update every object in a queryset"""

        success_count = 0
        warning_count = 0
        error_count = 0

        with Progress() as progress:
            task = progress.add_task(
                self.LOG_PREFIX + " [orange_red1]Updating objects...",
                total=db_queryset.count(),
            )
            for db_obj in db_queryset:
                if db_obj.woocommerceid:
                    try:
                        self.update_object_from_api(db_obj)
                        success_count += 1
                    except Exception as e:
                        self.log(
                            "[red]Object update failed with exception {}".format(e)
                        )
                        error_count += 1
                else:
                    warning_count += 1
                progress.update(task, advance=1)
            progress.stop_task(task)

        if request is not None:
            self._add_request_messages_from_update_counts(
                request, success_count, warning_count, error_count
            )

        return success_count, warning_count, error_count

    def _post_process_imported_objects(
        self, db_obj__wc_obj_list: list[tuple[object, dict]]
    ):
        """Post-process imported objects after all objects have been imported"""
        ...

    def import_all_objects_from_api(self, request=None) -> int:
        """Import new products from WooCommerce

        Returns: number of imported products
        """

        with Progress() as progress:
            task_prepare = progress.add_task(
                self.LOG_PREFIX + " [orange_red1]Preparing object download...", total=1
            )

            excludeids = ",".join(
                [
                    str(obj.woocommerceid)
                    for obj in self.MODEL.objects.all().exclude(woocommerceid=0)
                ]
            )
            wc_objects = []

            progress.update(task_prepare, advance=1)
            progress.stop_task(task_prepare)

            task_download = progress.add_task(
                self.LOG_PREFIX + " [green]Downloading objects..."
            )

            r = self.wcapi.get(f"{self.WC_API_BASEURL}?exclude={excludeids}")
            wc_objects += r.json()

            progress.update(
                task_download, advance=1, total=int(r.headers["X-WP-TotalPages"])
            )

            for page in range(2, int(r.headers["X-WP-TotalPages"]) + 1):
                wc_objects += self.wcapi.get(
                    f"{self.WC_API_BASEURL}?exclude={excludeids}&page={page}"
                ).json()
                progress.update(task_download, advance=1)

            progress.stop_task(task_download)

            if wc_objects:
                db_wc_object_list = []

                task_process = progress.add_task(
                    self.LOG_PREFIX + " [cyan]Processing objects...",
                    total=len(wc_objects),
                )
                for wc_obj in wc_objects:
                    db_obj = self.create_object_from_data(wc_obj)
                    db_wc_object_list.append((db_obj, wc_obj))
                    progress.update(task_process, advance=1)
                progress.stop_task(task_process)

                self._post_process_imported_objects(db_wc_object_list)

        if request is not None:
            self._add_request_messages_from_import_counts(request, len(wc_objects))
        return len(wc_objects)

    # Messages

    def _add_request_messages_from_update_counts(
        self, request, success_count: int, warning_count: int, error_count: int
    ):
        """Create messages from bulk update counts"""

        if success_count:
            messages.success(
                request,
                ngettext(
                    "%(count)d %(name)s object was updated from WooCommerce.",
                    "%(count)d %(name)s objects were updated from WooCommerce",
                    success_count,
                )
                % {
                    "count": success_count,
                    "name": self.MODEL._meta.verbose_name,
                },
            )
        if warning_count:
            messages.warning(
                request,
                ngettext(
                    "%(count)d %(name)s object is not linked to a WooCommerce object.",
                    "%(count)d %(name)s objects are not linked to a WooCommerce object.",
                    warning_count,
                )
                % {
                    "count": warning_count,
                    "name": self.MODEL._meta.verbose_name,
                },
            )
        if error_count:
            messages.error(
                request,
                ngettext(
                    "%(count)d %(name)s object couldn't be updated from WooCommerce. Was it deleted?",
                    "%(count)d %(name)s objects couldn't be updated from WooCommerce. Were they deleted?",
                    error_count,
                )
                % {
                    "count": error_count,
                    "name": self.MODEL._meta.verbose_name,
                },
            )

    def _add_request_messages_from_import_counts(self, request, success_count):
        messages.success(
            request,
            ngettext(
                "%(count)d new %(name)s object has been imported from WooCommerce!",
                "%(count)d new %(name)s objects have been imported from WooCommerce!",
                success_count,
            )
            % {
                "count": success_count,
                "name": self.MODEL._meta.verbose_name,
            },
        )
