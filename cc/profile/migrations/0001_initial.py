# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Profile'
        db.create_table('profile_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='profile', unique=True, to=orm['auth.User'])),
            ('name', self.gf('cc.general.models.VarCharField')(max_length=1000000000, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geo.Location'], null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('profile', ['Profile'])

        # Adding M2M table for field trusted_profiles on 'Profile'
        db.create_table('profile_profile_trusted_profiles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_profile', models.ForeignKey(orm['profile.profile'], null=False)),
            ('to_profile', models.ForeignKey(orm['profile.profile'], null=False))
        ))
        db.create_unique('profile_profile_trusted_profiles', ['from_profile_id', 'to_profile_id'])

        # Adding model 'Settings'
        db.create_table('profile_settings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('profile', self.gf('django.db.models.fields.related.OneToOneField')(related_name='settings', unique=True, to=orm['profile.Profile'])),
            ('email', self.gf('cc.general.models.EmailField')(max_length=254, blank=True)),
            ('endorsement_limited', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('send_notifications', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('feed_radius', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('feed_trusted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('profile', ['Settings'])

        # Adding model 'Invitation'
        db.create_table('profile_invitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_profile', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invitations_sent', to=orm['profile.Profile'])),
            ('to_email', self.gf('cc.general.models.EmailField')(max_length=254)),
            ('endorsement_weight', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('endorsement_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('code', self.gf('cc.general.models.VarCharField')(unique=True, max_length=1000000000)),
        ))
        db.send_create_signal('profile', ['Invitation'])

    def backwards(self, orm):
        # Deleting model 'Profile'
        db.delete_table('profile_profile')

        # Removing M2M table for field trusted_profiles on 'Profile'
        db.delete_table('profile_profile_trusted_profiles')

        # Deleting model 'Settings'
        db.delete_table('profile_settings')

        # Deleting model 'Invitation'
        db.delete_table('profile_invitation')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'geo.location': {
            'Meta': {'object_name': 'Location'},
            'city': ('cc.general.models.VarCharField', [], {'max_length': '1000000000', 'blank': 'True'}),
            'country': ('cc.general.models.VarCharField', [], {'max_length': '1000000000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'neighborhood': ('cc.general.models.VarCharField', [], {'max_length': '1000000000', 'blank': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'geography': 'True'}),
            'state': ('cc.general.models.VarCharField', [], {'max_length': '1000000000', 'blank': 'True'})
        },
        'profile.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'code': ('cc.general.models.VarCharField', [], {'unique': 'True', 'max_length': '1000000000'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'endorsement_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'endorsement_weight': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'from_profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invitations_sent'", 'to': "orm['profile.Profile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'to_email': ('cc.general.models.EmailField', [], {'max_length': '254'})
        },
        'profile.profile': {
            'Meta': {'object_name': 'Profile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['geo.Location']", 'null': 'True', 'blank': 'True'}),
            'name': ('cc.general.models.VarCharField', [], {'max_length': '1000000000', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'blank': 'True'}),
            'trusted_profiles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'trusting_profiles'", 'blank': 'True', 'to': "orm['profile.Profile']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'profile.settings': {
            'Meta': {'object_name': 'Settings'},
            'email': ('cc.general.models.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'endorsement_limited': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'feed_radius': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'feed_trusted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'settings'", 'unique': 'True', 'to': "orm['profile.Profile']"}),
            'send_notifications': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['profile']