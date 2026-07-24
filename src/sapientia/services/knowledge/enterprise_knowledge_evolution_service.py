"""Compares immutable Enterprise Knowledge versions and explains material change."""
from __future__ import annotations
from typing import Any
from sapientia.db.connection import get_engine
from sapientia.repositories.knowledge.knowledge_evolution_repository import EnterpriseKnowledgeEvolutionRepository

class EnterpriseKnowledgeEvolutionService:
    CATEGORIES=('datasets','columns','dataset_profiles','column_semantics','enterprise_objects','relationships','processes','concepts')
    IDS={
      'datasets':('dataset_id','name'),'columns':('column_id','name'),
      'dataset_profiles':('dataset_id','dataset_profile_id'),'column_semantics':('column_id','column_semantic_id'),
      'enterprise_objects':('canonical_key','enterprise_object_id'),
      'relationships':('source_enterprise_object_id','target_enterprise_object_id','relationship_type_code'),
      'processes':('process_key','business_process_id'),'concepts':('concept_name','enterprise_concept_id')
    }

    def compare_with_previous(self,current_knowledge_version_id:int,project_id:int=1)->dict[str,Any]:
        engine=get_engine()
        with engine.begin() as connection:
            repo=EnterpriseKnowledgeEvolutionRepository(connection)
            current=repo.version(current_knowledge_version_id,project_id)
            if not current: raise ValueError('Current Enterprise Knowledge version was not found.')
            previous=repo.previous(current_knowledge_version_id,project_id)
            if not previous:
                return {'comparison_created':False,'reason':'This is the first Enterprise Knowledge version for the business domain.',
                        'current_knowledge_version_id':current_knowledge_version_id,'current_version':current['knowledge_version']}
            existing=repo.existing(previous['knowledge_version_id'],current_knowledge_version_id,project_id)
            return existing or self._compare(repo,previous,current,project_id)

    def get(self,comparison_id:int,project_id:int=1):
        engine=get_engine()
        with engine.connect() as connection:
            return EnterpriseKnowledgeEvolutionRepository(connection).get(comparison_id,project_id)

    def timeline(self,project_id:int,business_domain:str):
        engine=get_engine()
        with engine.connect() as connection:
            return EnterpriseKnowledgeEvolutionRepository(connection).timeline(project_id,business_domain)

    def status(self,project_id:int,business_domain:str):
        engine=get_engine()
        with engine.connect() as connection:
            return EnterpriseKnowledgeEvolutionRepository(connection).status(project_id,business_domain)

    def _compare(self,repo,previous,current,project_id):
        old_content=self._content(previous.get('snapshot_json'))
        new_content=self._content(current.get('snapshot_json'))
        changes=[]; counts={'ADDED':0,'CHANGED':0,'REMOVED':0,'UNCHANGED':0}
        for category in self.CATEGORIES:
            old={self._key(category,x):x for x in old_content.get(category,[]) or []}
            new={self._key(category,x):x for x in new_content.get(category,[]) or []}
            for key in sorted(set(old)|set(new)):
                change=self._change(category,key,old.get(key),new.get(key))
                changes.append(change); counts[change['change_type']]+=1
        material=counts['ADDED']+counts['CHANGED']+counts['REMOVED']
        summary=(f"Knowledge Version {current['knowledge_version']} contains {material} material change(s): "
                 f"{counts['ADDED']} added, {counts['CHANGED']} changed and {counts['REMOVED']} removed.")
        return repo.save(previous,current,project_id,counts,summary,changes)

    @staticmethod
    def _content(snapshot):
        if not isinstance(snapshot,dict):return {}
        return snapshot.get('content') if isinstance(snapshot.get('content'),dict) else snapshot

    def _key(self,category,item):
        values=[]
        for field in self.IDS[category]:
            value=item.get(field)
            if value not in (None,''): values.append(str(value).strip().lower())
        return '|'.join(values) or repr(sorted(item.items()))

    def _change(self,category,key,old,new):
        source=new or old or {}
        if old is None: change_type='ADDED'; fields=[]
        elif new is None: change_type='REMOVED'; fields=[]
        else:
            fields=sorted(k for k in set(old)|set(new) if self._normalise(old.get(k))!=self._normalise(new.get(k)))
            change_type='CHANGED' if fields else 'UNCHANGED'
        name=self._name(category,source)
        if change_type=='ADDED': summary=f"{name} was added to Enterprise Knowledge."
        elif change_type=='REMOVED': summary=f"{name} is no longer present in Enterprise Knowledge."
        elif change_type=='CHANGED': summary=f"{name} changed: {', '.join(fields)}."
        else: summary=f"{name} is unchanged."
        return {'item_category':category.upper(),'item_key':key,'change_type':change_type,'item_name':name,
                'changed_fields':fields,'change_summary':summary,'previous':old,'current':new}

    @staticmethod
    def _normalise(value):
        if isinstance(value,str):return value.strip()
        if isinstance(value,dict):return {k:EnterpriseKnowledgeEvolutionService._normalise(v) for k,v in sorted(value.items())}
        if isinstance(value,list):return [EnterpriseKnowledgeEvolutionService._normalise(v) for v in value]
        return value

    @staticmethod
    def _name(category,item):
        for field in ('canonical_name','concept_name','process_name','name','semantic_type','relationship_type_code','canonical_key'):
            if item.get(field):return str(item[field])
        return category.replace('_',' ').title()
