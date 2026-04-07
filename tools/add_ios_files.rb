#!/usr/bin/env ruby
# add_ios_files.rb — Add new Swift files to the Xcode project target.
#
# Run from the repo root after creating new .swift files outside of Xcode:
#   ruby tools/add_ios_files.rb
#
# Pass specific files as arguments:
#   ruby tools/add_ios_files.rb EventyayOrganizer/Models/Foo.swift
#
# Requires: gem install xcodeproj --user-install

require 'xcodeproj'

PROJECT_PATH = File.expand_path('../open-event-organizer-ios/EventyayOrganizer.xcodeproj', __FILE__)
TARGET_NAME  = 'EventyayOrganizer'
IOS_ROOT     = File.expand_path('../open-event-organizer-ios/EventyayOrganizer', __FILE__)

project = Xcodeproj::Project.open(PROJECT_PATH)
target  = project.targets.find { |t| t.name == TARGET_NAME }
abort "Target '#{TARGET_NAME}' not found" unless target

main_group = project.main_group[TARGET_NAME]

def find_or_create_group(parent, name)
  parent.children.find { |c| c.respond_to?(:name) && (c.name == name || c.path == name) } ||
    parent.new_group(name, name)
end

def add_file(group, filename, target)
  exists = group.children.find { |c| c.respond_to?(:path) && c.path == filename }
  if exists
    puts "  already in project: #{filename}"
    return
  end
  ref = group.new_reference(filename)
  target.add_file_references([ref])
  puts "  added: #{filename}"
end

# If specific files passed as arguments, add only those
files_to_add = ARGV.map { |f| File.expand_path(f) }.select { |f| f.end_with?('.swift') && File.exist?(f) }

if files_to_add.empty?
  # Auto-detect: find all .swift files on disk not in project
  all_project_paths = project.files.map(&:real_path).map(&:to_s)
  files_to_add = Dir.glob(File.join(IOS_ROOT, '**', '*.swift')).reject do |f|
    all_project_paths.include?(f)
  end
end

if files_to_add.empty?
  puts "Nothing to add — all Swift files are already in the project."
  exit 0
end

puts "Adding #{files_to_add.count} file(s) to #{TARGET_NAME}:"

files_to_add.each do |abs_path|
  # Build group path from relative path inside EventyayOrganizer/
  rel = abs_path.sub("#{IOS_ROOT}/", '')
  parts = rel.split('/')
  filename = parts.pop

  group = main_group
  parts.each { |part| group = find_or_create_group(group, part) }

  add_file(group, filename, target)
end

project.save
puts "\nProject saved: #{PROJECT_PATH}"
