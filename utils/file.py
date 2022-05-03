def get_block_file(data_dir, epoch, slot):
    return data_dir / str(epoch) / "blocks" / f"{slot}.json"

def get_leader_schedule_file(data_dir, epoch):
    return data_dir / str(epoch) / "leader_schedule.json"