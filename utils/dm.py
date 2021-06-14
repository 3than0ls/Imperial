async def dm(user, **kwargs):
    """functions the same as a send function"""
    dm = user.dm_channel
    if dm is None:
        dm = await user.create_dm()
    await dm.send(**kwargs)
