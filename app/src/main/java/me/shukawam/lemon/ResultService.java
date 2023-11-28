package me.shukawam.lemon;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;
import jakarta.transaction.Transactional;

@Singleton
public class ResultService {
    private static final Logger logger = LoggerFactory.getLogger(ResultService.class);
    private final ResultRepository resultRepository;

    @Inject
    public ResultService(ResultRepository resultRepository) {
        this.resultRepository = resultRepository;
    }

    @Transactional
    public boolean saveResult(String imageName, float badQuality, float goodQuality, float emptyBackground) {
        var entity = new AnalyzeImageResult(imageName, badQuality, goodQuality, emptyBackground);
        var image = resultRepository.findById(imageName);
        if (image.isPresent()) {
            logger.info("Duplicate key.");
            return false;
        }
        var savedResult = resultRepository.save(entity);
        if (savedResult == null) {
            logger.info("Saving result is failed.");
            return false;
        }
        logger.info("Saving result is success.");
        return true;
    }
}
