# chews: Cheap Workstation

This is the original objective of the chews project.

## Objective


Build the tools to make it possible to run a part-time workstation cheaper in the cloud than to own and run a physical computer.

Assumptions: the workstation in the cloud
   - is only running about 48h per week
   - has directly attached storage comparable in capacity to a desktop PC.

Conclusion: Infeasible with Google Compute Platform pricing as of 2017-08-28.  See [Feasibility Analysis](#feasibility-analysis) below.

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

## Feasibility analysis

We consider the following workstation configuration:
   - 4 cores
   - 16GB ram
   - 256 SSD system disk
   - 2000GB HDD for dataset
and the following usage parameters
   - 1000GB dataset
   - 64GB used on system disk
   - 16h of workstation usage.

As of 2017-08-28, the Google Compute Platform charges the following:
   - $0.19 per hour for n1-standard-4 VM (4 cores, 16GB ram)
   - $0.04 per core-hour for Windows Server licence
   - $0.17 per GB-month for SSD-backed block devices
   - $0.04 per GB-month for HDD-backed block devices
   - $0.026 per GB-month for block device snapshots
   - $0.02 per GB-month for Regional blob storage (zero transfer fee)
   - $0.01 per GB-month for Nearline blob storage
   - $0.01 per GB for Nearline retrieval

For simplicity, we ignore costs for ops on GCS blobs.


### Desktop PC

Assuming depreciation over 4 years, a workstation purchase cost of $1550 and GCS Nearline for off-site back up, we have annual amortised costs of
   - $387.50 for desktop depreciation
   - $120 for off-site back up on Nearline GCS
   - Total: $507.50


### Snapshot-based virtual workstation

Instead of a enthusiast spec desktop PC we assume a Chromebox is used instead.  Assuming a purchase cost of $160 for the Chromebox and depreciation over 4 years.

Using snapshots of block devices when the workstation is powered down, we have annualised amortised costs of
   - $40 for Chromebox depreciation
   - $158.08 for the bare VM
   - $133.12 for the Windows Server licence
   - $8.52 for the block device storage while the workstation is ON
   - $331.97 for snapshot storage
   - Total: $671.09


### Regional blob-backed caching virtual workstation

Again, assuming a Chromebox is used instead with a purchase cost of $160 and depreciation over 4 years.

To reduce latency for populating the cache, we assume that the block devices are created and the cache warmed up once per week.

Using a small SSD block device of 256GB to cache the dataset stored on Regional (hot) GCS storage, we have amortised costs of
   - $40 for Chromebox depreciation
   - $158.08 for the bare VM
   - $133.12 for the Windows Server licence
   - $5.80 for the block device storage
   - $19.97 for the snapshot of the SSD system disk
   - $240.00 for Regional GCS storage of the dataset
   - Total: $596.97

### Nearline blob-backed caching virtual workstation

Again, assuming a Chromebox is used instead with a purchase cost of $160 and depreciation over 4 years.

To reduce latency for populating the cache, we assume that the block devices are created and the cache warmed up once per week.  Note that we have to pay for transfer costs from Nearline to warm up the cache.  We assume that each week we retrieve 256GB from Nearline to warm up the cache.

Using a small SSD block device of 256GB to cache the dataset stored on Nearline (warm) GCS storage, we have amortised costs of
   - $40 for Chromebox depreciation
   - $158.08 for the bare VM
   - $133.12 for the Windows Server licence
   - $5.80 for the block device storage
   - $19.97 for the snapshot of the SSD system disk
   - $120.00 for Nearline GCS storage
   - $133.12 for Nearline retrieval
   - Total: $610.09