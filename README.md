# chews: Cheap Workstation

## Objective

Build the tools to make it possible to run a part-time workstation cheaper in the cloud than to own and run a physical computer.

Assumptions: the workstation in the cloud
   - is only running about 48h per week
   - has directly attached storage comparable in capacity to a desktop PC.
   
## Background

The motivating use case is as a replacement for my desktop PC which I do not even switch on most days.  I work from an office using employer-supplied computing hardware.  When I am at home in the evenings, the typical computing devices I use would be a phone, a tablet or a laptop.  I still keep a desktop for curating and editing photographs from my DSLR camera (and in theory the occasional personal programming project).  I like using a desktop for photo editing because of the comfort of large monitor(s) and cheap multi-terabyte storage.  However, public cloud is close to being able to replace my desktop PC (for my use case).

At the time of writing, an enthusiast-spec desktop PC costs $1000-$2000 (without monitors).  A specific data point: you can buy a Dell XPS 8920 SE (advertised as "New XPS Tower SE") for $1550 with Intel Core i7-7700K, Windows 10 Home, 16GB ram, 256GB SSD, 2TB HDD and NVIDIA GeForce GXT 1060 6GB graphics.

In contrast, it is possible to rent from Google a 4-core 16GB virtual machine (VM) for $0.19 per hour plus $0.16 per hour for a Windows Server 2016 licence.  Together, the VM costs $0.35 per hour when it is switched on.  When the VM is switched off, you do not pay for these compute resources.

Clearly, this is not the complete story.  Block storage (i.e. disks) on public cloud is comparatively expensive.  Google currently charges $0.04 per gigabyte-month for an HDD-backed block device and you pay for the block storage even when the VM is powered down.  A 2TB block device would cost $80 per month.  Also, the Dell XPS Tower mentioned above has a graphics card which costs more than $300, if purchased by itself, whereas the comparison VM does not have a GPU.  Even keeping the GPU aside, if we naively add block devices to the VM, we lose its cost advantage.

Renting a workstation in the cloud has advantages beyond just cost.  Suppose you keep your desktop PC for 4 years; by the end of 4th year, you are using old hardware with performance that is no longer current.  The public cloud providers are continually upgrading their hardware and you will benefit from this incrementally.  You get to use the newer and faster processors as they are deployed by the providers.  Also, storage and memory historically have gotten cheaper over time.  If you own your own desktop, you will only benefit from hardware getting cheaper when you next buy hardware.  I am assuming the cloud providers will pass on hardware savings more aggressively in order to be competitive with each other in which case the same VM would cost less over time.

I have used Google as the example cloud provider.  Amazon and Microsoft have similar offerings and are priced similarly.

## Going cheaper

The main problem is the persistent storage.  Block devices are expensive because, at the moment, the cloud providers bundle storage bytes together with IO access.  A block device of 1TB comes with an expectation of supporting block-level IO performance of a hard disk (or SSD).  Google calls their product Persistent Disk, Amazon calls it EBS and Microsft just calls it Disk storage.

In my specific use case, where the VM is switched off most of the time, only the persistent storage aspect is important.  While the VM is switched off, the block-level IO performance is not a concern.

There is a better storage solution for when the VM is switched off: blob storage.  Google calls their product GCS, Amazon calls it S3 and Microsoft just calls it Blob storage.  Blob is cheaper than block device storage because it is persistent storage without the block-level IO expectations of block devices and you pay only for data stored.  With regards to the last point, for a block device, you pay for every byte on the device: for example, you pay 2TB for a 2TB block device even if there is only 1TB of data on the block device. 

Another related public cloud feature is block device snapshots.  It is possible to make a snapshot of a block device and later restore from it.  The Google documentation assumes a back up use case, however, it is possible to intentionally delete the original block device and later restore to a new block device.  Snapshots are cheaper, presumably, for at least two reasons:
   - a snapshot is storage without IO (so it is closer to blob storage in this respect)
   - a snapshot stores only the used blocks on a block device (assuming support from the operating system and its file system).
   
Current example Google prices (actual price varies by region):
   - Snapshots cost $0.026 per gigabyte-month
   - Blob storage costs $0.026 per gigabyte-month for "hot" storage class (called Multi-Regional)
   - and $0.01 per gigabyte-month for "warm" storage class (called Nearline).
   
Woah, 1TB of snapshots will cost $26 per month which will cost $1248 after 4 years (assuming prices do not reduce)!

This is correct.  However, if you are already backing up your desktop to the cloud as an off-site back up, then you can invert the desktop-cloud-backup relationship.  You can keep a hard disk at home with a back up of your cloud workstation; you pay for storage of live data in the cloud and keep the back up at home.
   
## Proposed solutions

### Snapshot solution

The easy solution uses snapshots.  Here are the main workflows:
   - Dessicate
      1. switch off VM
      1. snapshot all block devices
      1. delete block devices and VM
   - Rehydrate
      1. create block devices restoring from snapshots
      1. create VM using newly restored block devices
      1. switch on VM.
      
Returning to the use case, suppose I intend to use my workstation in the cloud over the weekend.  At the beginning of the weekend, I Rehydrate after which I can remotely connect and use the workstation; I pay for the VM and its block devices by the hour.  At the end of the weekend, I Dessicate.  At this point, I only pay for the snapshot storage.
      
The advantage is that there is no need to build any new infrastructure.  This just reuses whatever the cloud providers have already built and can be implemented with a bit of scripting.  (In fact, I am sure such scripts already exist).  It is relatively cheap, even for SSD-backed block devices.  You pay for the SSD-block devices when the VM is running and when it is switched off, you pay only for snapshot storage.

### Blob-backed caching solution

The more adventurous solution builds a filesystem whose data is persisted in blob storage but some (but not necessarily all) data is cached on a block device while the VM is running.  Before the block device can be deleted, the cached data must be flushed back to the backing blob storage.

We can even reduce the hourly cost of the running workstation by provisioning a smaller block device for caching.

For this specific use case, we can simplify the solution by making some assumptions:
   - the file system is intended to be mounted by one VM at a time
   - the file system can completely control the layout of data in blob storage.
This means that the solution does not need to worry about cache coherence.
