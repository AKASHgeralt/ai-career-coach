"""Avatar storage and serving.

Avatars used to be files under uploads/avatars behind a StaticFiles mount. The
hosting targets restart on idle and on deploy, which emptied that directory
while users.avatar_url kept pointing into it, so every restart turned avatars
into broken images. These tests pin the replacement: the bytes round-trip
through the database, so nothing depends on a writable or persistent disk.
"""
import pytest

pytestmark = pytest.mark.integration

# Smallest valid PNG and JPEG headers the sniffer accepts.
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff" + b"\x00" * 64


def _upload(client, auth, data=PNG, name="me.png", mime="image/png"):
    return client.post("/api/users/me/avatar", headers=auth,
                       files={"file": (name, data, mime)})


class TestAvatarUpload:
    def test_upload_returns_a_url_that_serves_the_image_back(self, client, auth):
        r = _upload(client, auth)
        assert r.status_code == 200
        url = r.json()["avatar_url"]
        assert url and url.startswith("/api/users/")

        got = client.get(url)
        assert got.status_code == 200
        assert got.content == PNG
        assert got.headers["content-type"] == "image/png"

    def test_content_type_follows_the_actual_bytes(self, client, auth):
        # Sniffed from the header, not from the filename the client sent.
        url = _upload(client, auth, JPEG, name="lying.png", mime="image/png").json()["avatar_url"]
        assert client.get(url).headers["content-type"] == "image/jpeg"

    def test_url_changes_when_the_image_changes(self, client, auth):
        first = _upload(client, auth, PNG).json()["avatar_url"]
        second = _upload(client, auth, JPEG, name="me.jpg").json()["avatar_url"]
        # A cached copy of the old avatar must not survive a replacement.
        assert first != second

    def test_replacing_an_avatar_serves_the_new_bytes(self, client, auth):
        _upload(client, auth, PNG)
        url = _upload(client, auth, JPEG, name="me.jpg").json()["avatar_url"]
        assert client.get(url).content == JPEG

    def test_rejects_a_non_image(self, client, auth):
        r = _upload(client, auth, b"%PDF-1.4 not an image", name="x.png")
        assert r.status_code == 400

    def test_rejects_an_oversize_image(self, client, auth):
        r = _upload(client, auth, PNG + b"\x00" * (3 * 1024 * 1024))
        assert r.status_code == 400

    def test_requires_authentication(self, client):
        r = client.post("/api/users/me/avatar", files={"file": ("me.png", PNG, "image/png")})
        assert r.status_code in (401, 403)


class TestAvatarRemoval:
    def test_delete_clears_the_url_and_stops_serving(self, client, auth):
        url = _upload(client, auth).json()["avatar_url"]
        assert client.delete("/api/users/me/avatar", headers=auth).json()["avatar_url"] is None
        assert client.get(url).status_code == 404


class TestAvatarServing:
    def test_unknown_user_is_404_not_500(self, client):
        r = client.get("/api/users/00000000-0000-0000-0000-000000000000/avatar")
        assert r.status_code == 404

    def test_malformed_id_is_422_not_500(self, client):
        assert client.get("/api/users/not-a-uuid/avatar").status_code == 422

    def test_user_without_an_avatar_is_404(self, client, auth):
        me = client.get("/api/users/me", headers=auth).json()
        assert client.get(f"/api/users/{me['id']}/avatar").status_code == 404
