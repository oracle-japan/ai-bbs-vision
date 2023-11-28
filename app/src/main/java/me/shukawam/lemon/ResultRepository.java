package me.shukawam.lemon;

import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.CrudRepository;

@Repository
public interface ResultRepository extends CrudRepository<AnalyzeImageResult, String> {
    
}
