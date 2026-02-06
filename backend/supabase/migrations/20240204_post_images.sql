-- Add image_url to posts table
alter table public.posts add column if not exists image_url text;

-- Storage Policies for post_images bucket
-- Ensure the bucket exists and is public
insert into storage.buckets (id, name, public)
values ('post_images', 'post_images', true)
on conflict (id) do update set public = true;

-- 1. Allow public access to read images
create policy "Public Access"
on storage.objects for select
using ( bucket_id = 'post_images' );

-- 2. Allow authenticated users to upload images
create policy "Authenticated Upload"
on storage.objects for insert
with check (
  bucket_id = 'post_images' AND
  auth.role() = 'authenticated'
);

-- 3. Allow users to delete their own images (optional but recommended)
create policy "Individual Delete"
on storage.objects for delete
using (
  bucket_id = 'post_images' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
