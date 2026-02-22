from .models import Profile,Identity

def apply_event(event):
    if event.event_type == "update_profile_image":
        identity= Identity.objects.get(public_key=event.public_key)
        profile, created = Profile.objects.get_or_create(identity=identity)
        profile.image_hash = event.payload["image_hash"]
        profile.save()
    # elif event.event_type == "create_listing":
    #     Listing.objects.create(
    #         id=event.payload["listing_id"],
    #         owner_key=event.public_key,
    #         price=event.payload["price"],
    #         item=event.payload["item"]
    #     )

    # elif event.event_type == "execute_trade":
    #     Trade.objects.create(
    #         listing_id=event.payload["listing_id"],
    #         buyer_key=event.public_key
    #     )
