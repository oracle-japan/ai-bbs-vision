package me.shukawam.lemon;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity(name = "results")
@Table(name = "results")
public class AnalyzeImageResult {
    @Id
    @Column(name = "image_name")
    private String imageName;
    @Column(name = "bad_quality")

    private float badQuality;
    @Column(name = "good_quality")
    private float goodQuality;

    @Column(name = "empty_background")
    private float emptyBackground;

    public AnalyzeImageResult() {
    }

    public AnalyzeImageResult(String imageName, float badQuality, float goodQuality, float emptyBackground) {
        this.imageName = imageName;
        this.badQuality = badQuality;
        this.goodQuality = goodQuality;
        this.emptyBackground = emptyBackground;
    }

    public String getImageName() {
        return imageName;
    }

    public void setImageName(String imageName) {
        this.imageName = imageName;
    }

    public float getBadQuality() {
        return badQuality;
    }

    public void setBadQuality(float badQuality) {
        this.badQuality = badQuality;
    }

    public float getGoodQuality() {
        return goodQuality;
    }

    public void setGoodQuality(float goodQuality) {
        this.goodQuality = goodQuality;
    }

    public float getEmptyBackground() {
        return emptyBackground;
    }

    public void setEmptyBackground(float emptyBackground) {
        this.emptyBackground = emptyBackground;
    }

}
